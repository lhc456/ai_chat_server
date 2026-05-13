from app.models.schemas import ChecklistRequest


class ChecklistService:
    @staticmethod
    async def build_checklist(request: ChecklistRequest) -> list[str]:
        items = ["手机", "钱包", "钥匙"]
        if request.purpose == "上班":
            items.extend(["工作证", "笔记本电脑"])
        elif request.purpose == "旅游":
            items.extend(["换洗衣物", "充电宝"])

        if request.additional:
            items.append(request.additional)

        return items
