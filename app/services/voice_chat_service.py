"""
语音对话服务

提供两条独立的基础能力（不依赖 AI）：
- audio → text  语音识别（ASR）
- text → audio  语音合成（TTS）

以及一条完整管线（依赖 Ollama AI，需要配置开启）：
- audio → text → AI → audio  语音对话
"""
import datetime
import json
import re
import time
from typing import AsyncGenerator

from app.clients import asr_client, tts_client
from app.core.config import settings
from app.models.schemas import SynthesizeResponse, TranscribeResponse, VoiceChatResponse

# 系统提示词：把 AI 定位成音箱助手，回复简短口语化（语音播报太长体验差）
# 情感要点：文本的情绪决定语音的感情——带语气词、口语断句，合成出来才不像机器人
SYSTEM_PROMPT = (
    "你是家里智能音箱的语音助手，性格热情开朗，像一个熟悉的朋友在聊天。"
    "要求："
    "① 真实性第一，任何回答都不能有虚假信息：不知道就说不知道，做不到就说做不到，"
    "绝不假装执行了没执行的动作（如假装播放歌曲），绝不编造事实、数据、地名、人名、作品名；"
    "涉及事实性问题时优先调工具核实，宁可说「我不确定」也不编答案；"
    "② 回答一般控制在 30~60 字；需要讲步骤、原理时可展开，仍不超过 300 字，宁短勿长；口语化、分句清楚，别念经；"
    "③ 适当用语气词（呀、哦、呢、嘛、哈、嗯）和口语表达（特好、特棒、没问题、放心吧）；"
    "④ 语调有起伏，重要的话可以带点感叹，遇到安慰、提醒时语气放轻放暖；"
    "⑤ 严禁输出任何 emoji 表情符号和 markdown 格式（会被语音合成念出怪音）；不要书面语和长句堆叠，断句要符合说话节奏。"
    "⑥ 调 web_search 时把搜索词写具体（带上主题、必要的时间和地点），不要用「最近」「最新」这种模糊词。"
    "⑦ 报天气固定用这个顺序：天气现象 → 今日最低~最高温度 → 当前温度 → 建议 → 景点推荐；"
    "⑧ 语音识别可能出错字：遇到明显不存在的歌手/歌曲/地名等专有名词，先按发音推断正确的写法再回答（如识别成「周年轮的青花池」，应理解为歌手周杰伦的歌曲《青花瓷》），并用正确名称回应，不要顺着错误字面编造不存在的歌手或歌曲；"
    "⑨ 建议必须结合当天实际情况灵活推理，禁止每次套同一句模板："
    "周末且温度舒适就鼓励出门活动；气温高（≥32度）就提醒防晒补水并推荐室内安排；"
    "有雨提醒带伞推室内；工作日早晚出门就提通勤注意；降水概率高也提前说；"
    "工具结果里给了景点参考就自然带出来，景点名必须用工具结果里的原名，严禁自己编造或替换其他地名；"
    "例：「今天杭州晴，今天21到31度，现在26度，周末天气挺舒服的，适合出门走走，可以去西湖沿苏堤白堤逛逛」"
)


# 工具定义（Ollama tools 格式）：LLM 自己判断何时调用哪个
WEATHER_TOOL = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": (
            "查询中国城市的天气，支持过去/今天/未来。day 参数传日期偏移："
            "今天=0，明天=1，后天=2，昨天=-1，前天=-2，大后天=3，以此类推；"
            "用户问「这周末」就折算成最近的周六对应的偏移。不传默认 0"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市名，如：杭州。用户没说城市时传空字符串"},
                "lat": {"type": "number", "description": "纬度，有设备定位时传，否则省略"},
                "lon": {"type": "number", "description": "经度，有设备定位时传，否则省略"},
                "day": {
                    "type": "string",
                    "description": "日期偏移：今天=0，明天=1，后天=2，昨天=-1，前天=-2；不传默认 0",
                },
            },
            "required": ["city"],
        },
    },
}

SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": (
            "联网搜索最新信息。当用户问到做饭菜谱、生活常识、专业知识、"
            "新闻时事、你不确定的事实性问题时调用，传入一句自然的搜索词"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索词，如：红烧肉怎么做不腻"},
            },
            "required": ["query"],
        },
    },
}

SPOTS_TOOL = {
    "type": "function",
    "function": {
        "name": "find_local_spots",
        "description": (
            "查找用户所在城市/附近值得去的地方（景点、公园、美食、逛街）。"
            "仅当用户明确问「去哪玩/附近有什么/有什么好玩的地方/推荐个地方」时才调用；"
            "普通问天气不要调用，天气工具结果里已含生活建议"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市名，用户没说时传空字符串"},
                "lat": {"type": "number", "description": "纬度，有定位时传"},
                "lon": {"type": "number", "description": "经度，有定位时传"},
                "tomorrow": {"type": "boolean", "description": "用户问的是明天的事则传 true"},
            },
            "required": ["city"],
        },
    },
}

# Agent 工具箱：新增工具在这里注册，执行器在 _execute_tool_call 里加分支
AGENT_TOOLS = [WEATHER_TOOL, SEARCH_TOOL, SPOTS_TOOL]


def _resolve_day_offset(day: str) -> int:
    """
    把 LLM 传来的语义化日期折算成日期偏移（今天=0，明天=1，昨天=-1…）

    支持：today/tomorrow/yesterday/day_after_tomorrow/后夭 等英文关键词，
    以及「+2」「-1」这类数字形式；中文由模型翻译成关键词（工具描述已给映射）。
    """
    mapping = {
        "today": 0, "now": 0,
        "tomorrow": 1,
        "day_after_tomorrow": 2,
        "yesterday": -1,
        "day_before_yesterday": -2,
    }
    if day in mapping:
        return mapping[day]
    try:
        return int(day)  # 直接传偏移数字也支持
    except (TypeError, ValueError):
        return 0


async def _execute_weather(args: dict, session_loc: dict | None, default_city: str) -> str:
    """执行天气工具调用：城市 > 会话定位 > 默认城市；返回喂给 LLM 的中文结果"""
    from app.clients import weather_client

    city = (args.get("city") or "").strip()
    lat, lon = args.get("lat"), args.get("lon")

    # 对话里没说城市 → 优先用设备定位，再退默认城市
    if not city:
        if session_loc:
            lat = lat if lat is not None else session_loc.get("lat")
            lon = lon if lon is not None else session_loc.get("lon")
            city = session_loc.get("city") or "当前位置"
        else:
            city = default_city

    # 用户问的是哪天：语义化日期（today/tomorrow/yesterday/weekend…）→ 统一折算成日期偏移
    day = (args.get("day") or "today").strip()
    offset = _resolve_day_offset(day)

    w = await weather_client.get_weather(city, lat=lat, lon=lon)
    result = weather_client.format_weather(w, day=str(offset))

    # 第 1 层：活动/生活建议（按目标日期的天气/温度/星期生成，不再永远用“此刻”）
    try:
        from app.clients import activity_client
        now = datetime.datetime.now()
        target_date = datetime.date.today() + datetime.timedelta(days=offset)
        day_data = w["days"][max(0, min(len(w["days"]) - 1, offset + 2))]
        # 过去日期用当天气温中位数；今天用当前实测温度；未来用区间中位数
        temp = w["current"]["temp"] if offset == 0 else (day_data["min"] + day_data["max"]) / 2
        tips = activity_client.get_activity_tips(
            day_data["desc"], temp, target_date.month, target_date.weekday(), now.hour
        )
        if tips:
            result += f"；{tips}"
    except Exception:
        pass  # 活动建议失败不影响天气主流程

    # 地点推荐不再默认拼进天气回答——门控到 find_local_spots 工具里，
    # 用户明确问「去哪玩/附近有什么」才推（不推荐也是一种合理）
    return result


async def _execute_tool_call(name: str, args: dict, session_loc: dict | None) -> str:
    """工具执行器：按名字分发到对应客户端；单工具失败不影响整轮对话"""
    if name == "get_weather":
        return await _execute_weather(args, session_loc, settings.default_city)
    if name == "web_search":
        from app.clients import search_client
        query = (args.get("query") or "").strip()
        if not query:
            return "搜索词为空"
        return await search_client.search_web(query)
    if name == "find_local_spots":
        return await _find_local_spots(args, session_loc, settings.default_city)
    return f"未知工具：{name}"


async def _find_local_spots(args: dict, session_loc: dict | None, default_city: str) -> str:
    """
    「去哪玩/附近有什么」专用工具（地点推荐门控：只有用户明确问才调用）

    三层降级链路（ROADMAP 建议系统三层化）：
      自定义地点 → Exa 动态搜当地特色 → 静态库 → 全无则提示只给生活建议
    """
    from app.clients import poi_client, search_client, weather_client

    city = (args.get("city") or "").strip()
    lat, lon = args.get("lat"), args.get("lon")

    if not city:
        if session_loc:
            lat = lat if lat is not None else session_loc.get("lat")
            lon = lon if lon is not None else session_loc.get("lon")
            city = session_loc.get("city") or "当前位置"
        else:
            city = default_city

    # 反查区（就近推荐用）
    district = None
    if lat is not None and lon is not None:
        loc = await weather_client.reverse_district(lat, lon)
        if loc and loc[1]:
            district = loc[1]

    now = datetime.datetime.now()
    is_tomorrow = bool(args.get("tomorrow"))

    # 先查一下当地天气，筛选晴雨/温度（复用 get_weather 的缓存）
    try:
        w = await weather_client.get_weather(city, lat=lat, lon=lon)
        code, tmax = w["today"]["code"], w["today"]["max"]
    except Exception:
        code, tmax = 1, 25  # 查不到天气按舒适晴天处理，不阻断推荐

    # ①+② 自定义地点 → 静态库
    result = poi_client.recommend(
        city, district, code, tmax, now.month, now.weekday(), now.hour,
        is_tomorrow=is_tomorrow,
        # 库里没这个城市时进入「乡下模式」：只用自定义地点，不硬凑
        custom_only=city.rstrip("市") not in poi_client._LIBRARY and not district,
    )
    if result:
        return result

    # ③ Exa 动态搜当地特色（静态库没有的城市）
    dynamic = await search_client.search_local_spots(city, now.month)
    if dynamic:
        return f"搜到的{city}热门去处参考：{dynamic[:200]}"

    # 全无 → 明确告知走生活建议
    return f"{city}没有找到合适的景点信息，结合天气给些生活活动建议就好，不要提具体地点"


# 按句切分：中文标点后断句，问号/叹号/省略号都算句尾；
# 逗号过长时也切（避免长句迟迟不出的情况）
_SENTENCE_SPLIT = re.compile(r"(?<=[。！？；!?;~～…])(?=[^\s])")
_MAX_SUB_LEN = 22  # 单个分段超过这个长度时在逗号处再切一刀


def _split_sentences(buffer: str) -> list[str]:
    """把累计文本切成「完整句 + 未完部分」两段，返回 [完整句列表, 剩余文本]"""
    parts = _SENTENCE_SPLIT.split(buffer)
    done, tail = parts[:-1], parts[-1]
    # 长句在逗号处补切，让首句更快出来
    out: list[str] = []
    for seg in done:
        seg = seg.strip()
        if not seg:
            continue
        while len(seg) > _MAX_SUB_LEN:
            cut = seg.rfind("，", 0, _MAX_SUB_LEN)
            if cut <= 0:
                break
            out.append(seg[: cut + 1])
            seg = seg[cut + 1 :]
        if seg:
            out.append(seg)
    return out, tail.strip()


class VoiceChatService:
    @staticmethod
    async def audio_to_text(audio_bytes: bytes) -> TranscribeResponse:
        """语音识别：录音 → 文字（不依赖 AI，始终可用）"""
        start = time.time()
        text = await asr_client.transcribe(audio_bytes)
        if not text:
            raise ValueError("未能识别出有效语音内容")
        return TranscribeResponse(
            text=text,
            elapsed_ms=int((time.time() - start) * 1000),
        )

    @staticmethod
    async def text_to_audio(text: str) -> SynthesizeResponse:
        """语音合成：文字 → 语音（不依赖 AI，始终可用）"""
        start = time.time()
        audio = await tts_client.synthesize(text)
        return SynthesizeResponse(
            audio=audio,
            elapsed_ms=int((time.time() - start) * 1000),
        )

    @staticmethod
    async def streaming_conversation(
        audio_bytes: bytes,
        history: list[dict] = None,
        session_loc: dict = None,
    ) -> AsyncGenerator[dict, None]:
        """
        全链路流式对话：ASR → LLM 逐 token（带工具调用）→ 按句切分 → 每句立刻 TTS

        工具循环：模型要天气数据时，执行 get_weather 把真实数据喂回去重新生成；
        最多循环 3 次防失控。

        事件流（dict）:
            {"type": "user",     "text": str}                  识别结果
            {"type": "sentence", "text": str, "audio": bytes}  一句话及其语音
            {"type": "done",     "text": str, "elapsed_ms": int} 全文与总耗时

        Args:
            history: 历史消息（[{role, content}]），可为空
            session_loc: 会话定位 {"lat", "lon", "city"}，问天气没说城市时用
        """
        from app.clients.ollama_client import OllamaClient

        start = time.time()

        # 1. ASR：语音 → 文字
        user_text = await asr_client.transcribe(audio_bytes)
        if not user_text:
            raise ValueError("未能识别出有效语音内容")
        yield {"type": "user", "text": user_text}

        # 2. LLM 流式生成 + 工具调用 + 按句切分
        # 把当前时间写进系统提示：模型记忆会过期，时间问题（今天是几号/最近新闻）靠它纠偏
        now = datetime.datetime.now()
        weekday_cn = "一二三四五六日"[now.weekday()]
        system_content = (
            SYSTEM_PROMPT
            + f"\n现在是 {now.year}年{now.month}月{now.day}日 星期{weekday_cn} {now.hour:02d}:{now.minute:02d}。"
              "涉及「最近/今天/现在」的搜索词，把具体日期写进去。"
        )
        if session_loc:
            system_content += (
                f"\n用户当前位置：{session_loc.get('city')}。"
                "用户问天气但没说城市时，调 get_weather 不传 city 只传 lat/lon。"
            )
        else:
            system_content += (
                f"\n用户所在城市：{settings.default_city}。"
                "用户问天气但没说城市时，调 get_weather 就用这个城市。"
            )
        messages = [{"role": "system", "content": system_content}]
        messages += (history or [])[-6:]
        messages.append({"role": "user", "content": user_text})

        full_text = ""
        for _round in range(3):  # 工具循环上限，防失控
            buffer = ""
            tool_calls: list[dict] = []

            async for event in OllamaClient.stream_chat_reply(
                messages, tools=AGENT_TOOLS
            ):
                if event["type"] == "tool_call":
                    tool_calls.append(event)
                    continue
                buffer += event["content"]
                sentences, buffer = _split_sentences(buffer)
                for sentence in sentences:
                    full_text += sentence
                    # 每凑齐一句立刻合成，不等全文
                    audio = await tts_client.synthesize(sentence)
                    yield {"type": "sentence", "text": sentence, "audio": audio}

            # 模型没调工具：正常结束
            if not tool_calls:
                break

            # 把「模型发起调用」这条消息补进上下文，再执行工具、喂回结果
            assistant_msg = {"role": "assistant", "content": buffer, "tool_calls": [
                {
                    "function": {
                        "name": tc["name"],
                        "arguments": tc["arguments"]
                        if isinstance(tc["arguments"], dict)
                        else json.loads(tc["arguments"] or "{}"),
                    },
                }
                for tc in tool_calls
            ]}
            if buffer:
                assistant_msg["content"] = buffer
            else:
                assistant_msg.pop("content", None)
            messages.append(assistant_msg)

            for tc in tool_calls:
                try:
                    args = (
                        tc["arguments"]
                        if isinstance(tc["arguments"], dict)
                        else json.loads(tc["arguments"] or "{}")
                    )
                    result = await _execute_tool_call(tc["name"], args, session_loc)
                except Exception as e:
                    result = f"工具调用失败：{e}"
                messages.append({
                    "role": "tool",
                    "content": result,
                    "name": tc["name"],
                })
            # 继续下一轮：模型拿到真实数据后生成最终回复
        else:
            fallback = "这个问题我想了太久，换一个问法试试吧"
            full_text += fallback
            yield {
                "type": "sentence",
                "text": fallback,
                "audio": await tts_client.synthesize(fallback),
            }

        # 收尾：把最后没凑齐一句的余量也合成播出去
        tail = buffer.strip() if not tool_calls else ""
        if tail:
            full_text += tail
            audio = await tts_client.synthesize(tail)
            yield {"type": "sentence", "text": tail, "audio": audio}

        yield {
            "type": "done",
            "text": full_text,
            "elapsed_ms": int((time.time() - start) * 1000),
        }

    @staticmethod
    async def process(audio_bytes: bytes) -> VoiceChatResponse:
        """
        完整语音对话管线（需要 AI，配置 voice_ai_enabled=true 才能调用）

        录音 → ASR → Ollama 生成回复 → TTS → 返回语音
        """
        from app.clients.ollama_client import OllamaClient

        start = time.time()

        # 1. ASR：语音 → 文字
        user_text = await asr_client.transcribe(audio_bytes)
        if not user_text:
            raise ValueError("未能识别出有效语音内容")

        # 2. LLM：文字 → AI回复
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
        ]
        reply_text = await OllamaClient.create_chat_reply(messages)

        # 3. TTS：回复文字 → 语音
        audio_out = await tts_client.synthesize(reply_text)
        # 后续优化点：让 LLM 同时输出情绪标签，配合 Azure express-as 切换情感风格

        return VoiceChatResponse(
            user_text=user_text,
            reply_text=reply_text,
            audio=audio_out,
            elapsed_ms=int((time.time() - start) * 1000),
        )
