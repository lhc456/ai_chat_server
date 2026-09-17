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
    "① 简短口语化，不超过40个字，一般就一两句话；"
    "② 适当用语气词（呀、哦、呢、嘛、哈、嗯）和口语表达（特好、特棒、没问题、放心吧）；"
    "③ 语调有起伏，重要的话可以带点感叹，遇到安慰、提醒时语气放轻放暖；"
    "④ 严禁输出任何 emoji 表情符号和 markdown 格式（会被语音合成念出怪音）；不要书面语和长句堆叠，断句要符合说话节奏。"
    "⑤ 调 web_search 时把搜索词写具体（带上主题、必要的时间和地点），不要用「最近」「最新」这种模糊词。"
    "⑥ 报天气固定用这个顺序：天气现象 → 今日最低~最高温度 → 当前温度 → 建议 → 景点推荐；"
    "⑦ 建议必须结合当天实际情况灵活推理，禁止每次套同一句模板："
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
        "description": "查询中国城市的实时天气和今明两天预报，当用户问到天气、温度、下雨、穿衣、出行建议时调用",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市名，如：杭州。用户没说城市时传空字符串"},
                "lat": {"type": "number", "description": "纬度，有设备定位时传，否则省略"},
                "lon": {"type": "number", "description": "经度，有设备定位时传，否则省略"},
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

# Agent 工具箱：新增工具在这里注册，执行器在 _execute_tool_call 里加分支
AGENT_TOOLS = [WEATHER_TOOL, SEARCH_TOOL]


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

    w = await weather_client.get_weather(city, lat=lat, lon=lon)
    result = weather_client.format_weather(w)

    # 拼接就近场景化推荐（区级定位 + 星期/时段 + 天气筛选，垂直场景第一块拼图）
    try:
        from app.clients import poi_client

        district = None
        rec_city = w["city"]
        # 有定位时反查所在区，推荐就近去处；失败降级为全市推荐
        if lat is not None and lon is not None:
            loc = await weather_client.reverse_district(lat, lon)
            if loc and loc[1]:
                district = loc[1]  # 城市名可能为空，用天气查询的城市名兜底

        now = datetime.datetime.now()
        rec = poi_client.recommend(
            rec_city,
            district,
            w["today"]["code"],
            w["today"]["max"],
            now.month,
            now.weekday(),
            now.hour,
        )
        if rec:
            scope = f"（{rec_city}{district or ''}）" if district else f"（{rec_city}）"
            result += f"；{scope}{rec}"
    except Exception:
        pass  # 景点推荐失败不影响天气主流程
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
    return f"未知工具：{name}"


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
