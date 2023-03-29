from lib import itchat
from common.log import logger
import os
import json
from concurrent.futures import ThreadPoolExecutor

TEXT = 'Text'
thread_pool = ThreadPoolExecutor(max_workers=8)


class Channel(object):
    def startup(self):
        """
        init channel
        """
        raise NotImplementedError

    def handle_text(self, msg):
        """
        process received msg
        :param msg: message object
        """
        raise NotImplementedError

    def send(self, msg, receiver):
        """
        send message to user
        :param msg: message content
        :param receiver: receiver channel account
        :return:
        """
        raise NotImplementedError


@itchat.msg_register(TEXT)
def handler_single_msg(msg):
    WechatChannel().handle_text(msg)
    return None


@itchat.msg_register(TEXT, isGroupChat=True)
def handler_group_msg(msg):
    WechatChannel().handle_group(msg)
    return None


class WechatChannel(Channel):
    def __init__(self):
        self.userName = None
        self.nickName = None
        self.startup()

    def startup(self):

        itchat.instance.receivingRetryCount = 600  # 修改断线超时时间
        # login by scan QRCode
        hotReload = False
        try:
            itchat.auto_login(enableCmdQR=2, hotReload=hotReload)
        except Exception as e:
            if hotReload:
                logger.error("Hot reload failed, try to login without hot reload")
                itchat.logout()
                os.remove("itchat.pkl")
                itchat.auto_login(enableCmdQR=2, hotReload=hotReload)
            else:
                raise e
        self.userName = itchat.instance.storageClass.userName
        self.nickName = itchat.instance.storageClass.nickName
        logger.info("Wechat login success, username: {}, nickname: {}".format(self.userName, self.nickName))

    def send_msg_to_nickName(self, msg, nickName):
        receiverObj = itchat.search_friends(nickName=nickName)
        logger.info('[WX] receiverObj={}'.format(msg, str(receiverObj)))
        self.send(msg, receiver=receiverObj[0].UserName)

    def send_msg_to_groupName(self, msg, groupName):
        groupObj = itchat.search_chatrooms(name=groupName)
        logger.info('[WX] groupName={}'.format(msg, str(groupObj)))
        self.send(msg, receiver=groupObj[0].UserName)

    # handle_* 系列函数处理收到的消息后构造Context，然后传入handle函数中处理Context和发送回复
    # Context包含了消息的所有信息，包括以下属性
    #   type 消息类型, 包括TEXT、VOICE、IMAGE_CREATE
    #   content 消息内容，如果是TEXT类型，content就是文本内容，如果是VOICE类型，content就是语音文件名，如果是IMAGE_CREATE类型，content就是图片生成命令
    #   kwargs 附加参数字典，包含以下的key：
    #        session_id: 会话id
    #        isgroup: 是否是群聊
    #        receiver: 需要回复的对象
    #        msg: itchat的原始消息对象

    def handle_text(self, msg):
        logger.debug("[WX]receive text msg: " + json.dumps(msg, ensure_ascii=False))
        content = msg['Text']
        from_user_id = msg['FromUserName']
        to_user_id = msg['ToUserName']  # 接收人id
        try:
            other_user_id = msg['User']['UserName']  # 对手方id
        except Exception as e:
            logger.warn("[WX]get other_user_id failed: " + str(e))
            if from_user_id == self.userName:
                other_user_id = to_user_id
            else:
                other_user_id = from_user_id

    def handle_group(self, msg):
        logger.debug("[WX]receive group msg: " + json.dumps(msg, ensure_ascii=False))
        group_name = msg['User'].get('NickName', None)
        group_id = msg['User'].get('UserName', None)
        create_time = msg['CreateTime']  # 消息时间
        if not group_name:
            return ""
        origin_content = msg['Content']
        content = msg['Content']
        content_list = content.split(' ', 1)
        context_special_list = content.split('\u2005', 1)
        if len(context_special_list) == 2:
            content = context_special_list[1]
        elif len(content_list) == 2:
            content = content_list[1]

    # 统一的发送函数，每个Channel自行实现，根据reply的type字段发送不同类型的消息
    def send(self, msg, receiver):
        itchat.send(msg, toUserName=receiver)
        logger.info('[WX] sendMsg={}, receiver={}'.format(msg, receiver))


if __name__ == "__main__":
    WechatChannel().startup()
