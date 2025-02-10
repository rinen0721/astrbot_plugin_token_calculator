from yaml import NodeEvent

from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.core.message.components import Plain
from astrbot.core.provider.entites import ProviderRequest, LLMResponse


@register("TokenCalculator", "rinen0721", "计算并显示Token消耗的插件，部分provider可用", "1.0.0", "https://github.com/rinen0721/astrbot_plugin_token_calculator")
class TokenCalculator(Star):
    cacuToken:bool =True
    tokenMsg:str =""
    llmResponsed:bool=False #通过这个变量确定是llm请求之后的消息而不是指令


    def __init__(self, context: Context):
        super().__init__(context)

    # 注册指令的装饰器。指令名为 CacuToken。注册成功后，发送 `/CacuToken` 就会触发这个指令，并开启/关闭计算Token的功能
    @filter.command("CacuToken")
    async def CacuToken(self, event: AstrMessageEvent):
        """输入/CacuToken以开启/关闭Token计算"""  # 这是 handler 的描述，将会被解析方便用户了解插件内容。建议填写。
        self.cacuToken=not self.cacuToken
        if self.cacuToken:
            yield event.plain_result(f"开启计算Token功能") # 发送一条纯文本消息
        else:
            yield event.plain_result(f"关闭计算Token功能")  # 发送一条纯文本消息


    @filter.on_llm_response()
    async def on_llm_resp(self, event: AstrMessageEvent, resp: LLMResponse):  # 请注意有三个参数
        if self.cacuToken:
            try:
                completion=resp.raw_completion
                if completion is None:
                    self.tokenMsg="(无法获取Token用量信息，可能是当前provider不支持)"
                    return
                usage=completion.usage
                if usage is None:
                    self.tokenMsg = "(无法获取Token用量信息，可能是当前provider不支持)"
                    return
                completion_tokens=usage.completion_tokens
                prompt_tokens=usage.prompt_tokens
                total_tokens=usage.total_tokens
                self.tokenMsg=f"(completion_tokens:{completion_tokens},prompt_tokens:{prompt_tokens},token总消耗:{total_tokens})"
                self.llmResponsed=True
            except:
                self.tokenMsg = "(TokenCalculator插件无法获取信息或者出现未知错误)"


    @filter.on_decorating_result()
    async def on_decorating_result(self, event: AstrMessageEvent):
        if self.cacuToken and self.llmResponsed:
            try:
                result = event.get_result()
                chain = result.chain
                chain.append(Plain(self.tokenMsg))  # 在消息链的最后加上Token计算信息
                self.llmResponsed=False
            except:
                raise RuntimeError("CacuToken插件在回复消息的时候出现错误")
