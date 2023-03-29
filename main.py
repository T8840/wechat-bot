from wechat.wechat_channel import WechatChannel
from apscheduler.schedulers.blocking import BlockingScheduler


wechat_bot = WechatChannel()
def send_msg_to_group():
    wechat_bot.send_msg_to_groupName("hello","ChatGPT测试群")

def send_msg_to_friend():
    wechat_bot.send_msg_to_groupName("dd","friendNickName")

def run():
    # 创建一个调度器
    scheduler = BlockingScheduler()
    # 添加一个间隔作业，每隔 10 秒执行一次
    scheduler.add_job(send_msg_to_group, 'interval', seconds=10)
    # 开始调度器
    scheduler.start()

if __name__ == "__main__":
    run()
