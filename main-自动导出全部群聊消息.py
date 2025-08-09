from db.man import DatabaseManager
from nt_msg.message import Message
from db.models import GroupMessage
from pprint import pprint
import json

def export_all_chat_records():
    """
    自动查找所有群聊，并分别导出其聊天记录。
    """
    dbman = DatabaseManager()

    try:
        # 获取数据库中所有不同的群聊Uin
        all_group_uins = dbman.group_messages().with_entities(GroupMessage.groupUin).distinct().all()

        if not all_group_uins:
            print("数据库中没有找到任何群聊记录。")
            return

        print(f"找到 {len(all_group_uins)} 个群聊。开始导出...")

        # 遍历所有群聊Uin
        for uin_tuple in all_group_uins:
            target_group_uin = uin_tuple[0]
            print(f"\n--- 正在导出群聊 {target_group_uin} 的消息 ---")

            messages_query = dbman.group_messages().filter_by(groupUin=target_group_uin).order_by(GroupMessage.msgSeq)
            db_messages = messages_query.all()

            if not db_messages:
                print(f"群聊 {target_group_uin} 没有找到聊天记录。")
                continue

            processed_messages = []
            for dbo in db_messages:
                try:
                    msg_obj = Message.from_db(dbo)
                    processed_messages.append({
                        "msgId": msg_obj.ID,
                        "msgSeq": msg_obj.seq,
                        "elements": [str(elem) for elem in msg_obj.elements]
                    })
                except Exception as e:
                    print(f"处理消息ID {dbo.msgId} 时出错: {e}")
            
            output_filename = f"chat_history_{target_group_uin}.json"
            with open(output_filename, 'w', encoding='utf-8') as f:
                json.dump(processed_messages, f, ensure_ascii=False, indent=4)
            
            print(f"成功导出 {len(processed_messages)} 条记录到文件：{output_filename}")

        print("\n所有群聊聊天记录已导出完成。")

    except KeyError:
        print("错误：数据库会话 'nt_msg' 未正确初始化。请确认 'nt_msg.decrypt.db' 文件存在。")
    except Exception as e:
        print(f"发生未知错误: {e}")

if __name__ == "__main__":
    export_all_chat_records()