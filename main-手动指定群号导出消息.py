from db.man import DatabaseManager
from nt_msg.message import Message
from db.models import GroupMessage
from pprint import pprint
import json

def export_chat_records():
    """
    导出指定群聊的聊天记录。
    """
    # 实例化数据库管理器
    dbman = DatabaseManager()

    # 定义要查询的群Uin，群号改为实际群号
    target_group_uin = 群号

    try:
        # 查询所有 groupUin 等于目标Uin的群聊消息
        # 这里的 .order_by(GroupMessage.msgSeq) 可以确保消息按时间顺序排列
        messages_query = dbman.group_messages().filter_by(groupUin=target_group_uin).order_by(GroupMessage.msgSeq)
        
        # 获取查询结果，并将其转换为列表
        db_messages = messages_query.all()

        if not db_messages:
            print(f"没有找到 groupUin 为 {target_group_uin} 的聊天记录。")
            
            # 为了调试，我们打印所有群聊消息的总数
            total_messages_count = dbman.group_messages().count()
            print(f"数据库中共有 {total_messages_count} 条群聊消息。")
            return

        # 准备一个列表来存储处理后的消息
        processed_messages = []

        # 遍历数据库查询结果，使用 nt_msg.message 中的类来处理每一条消息
        for dbo in db_messages:
            # Message.from_db() 是根据您提供的 message.py 文件编写的，
            # 它负责将数据库对象（dbo）转换为更易读的 Message 对象
            try:
                msg_obj = Message.from_db(dbo)
                processed_messages.append({
                    "msgId": msg_obj.ID,
                    "msgSeq": msg_obj.seq,
                    "elements": [str(elem) for elem in msg_obj.elements] # 将元素转换为字符串
                })
            except Exception as e:
                print(f"处理消息ID {dbo.msgId} 时出错: {e}")

        # 示例 1: 打印到控制台
        # print(f"--- 找到 {len(processed_messages)} 条群聊消息 ---")
        # pprint(processed_messages)

        # 示例 2: 导出到 JSON 文件
        output_filename = f"chat_history_{target_group_uin}.json"
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(processed_messages, f, ensure_ascii=False, indent=4)
        print(f"\n聊天记录已成功导出到文件：{output_filename}")

    except KeyError:
        print("错误：数据库会话 'nt_msg' 未正确初始化。请确认 'nt_msg.decrypt.db' 文件存在。")
    except Exception as e:
        print(f"发生未知错误: {e}")

if __name__ == "__main__":
    export_chat_records()