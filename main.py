import os
import json
import csv
import argparse
from datetime import datetime
from db.man import DatabaseManager
from nt_msg.message import Message
from db.models import GroupMessage, PrivateMessage
import blackboxprotobuf


def export_group_chat_records(dbman, output_dir, export_format='json'):
    """
    导出所有群聊的聊天记录。
    """
    try:
        all_group_uins = dbman.group_messages().with_entities(GroupMessage.groupUin).distinct().all()
        if not all_group_uins:
            print("数据库中没有找到任何群聊记录。")
            return

        print(f"找到 {len(all_group_uins)} 个群聊。开始导出...")

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
                        "msgId": dbo.msgId,
                        "msgRandom": dbo.msgRandom,
                        "msgSeq": dbo.msgSeq,
                        "chatType": dbo.chatType,
                        "msgType": dbo.msgType,
                        "subMsgTypepb": dbo.subMsgType,
                        "sendType": dbo.sendType,
                        "peeruid": dbo.peerUid,
                        "peeruin": dbo.peerUin,
                        "sendStatus": dbo.sendStatus,
                        "msgTime": dbo.msgTime,
                        "sendMemberName": dbo.sendMemberName,
                        "sendNickName": dbo.sendNickName,
                        "senderQQNum": dbo.senderUin,
                        "replyMsgSeq": dbo.refSeq,
                        "elements": [str(elem) for elem in msg_obj.elements]
                    })
                except Exception as e:
                    print(f"处理消息ID {dbo.msgId} 时出错: {e}")
            
            output_filename = os.path.join(output_dir, f"group_chat_history_{target_group_uin}.{export_format}")
            
            if export_format == 'json':
                with open(output_filename, 'w', encoding='utf-8') as f:
                    json.dump(processed_messages, f, ensure_ascii=False, indent=4)
            elif export_format == 'txt':
                with open(output_filename, 'w', encoding='utf-8') as f:
                    for msg in processed_messages:
                        sender_name = msg.get("sendMemberName") or msg.get("sendNickName") or "未知发送人"
                        sender_qq = msg.get("senderQQNum")
                        message_content = "".join(msg.get("elements", []))
                        timestamp = datetime.fromtimestamp(msg.get("msgTime", 0)).strftime('%Y-%m-%d %H:%M:%S')
                        f.write(f"{sender_name}({sender_qq}): {message_content} ({timestamp})\n")
            elif export_format == 'csv':
                with open(output_filename, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(["msgId", "msgSeq", "senderName", "senderQQNum", "msgTime", "elements"])
                    for msg in processed_messages:
                        sender_name = msg.get("sendMemberName") or msg.get("sendNickName") or "未知发送人"
                        writer.writerow([
                            msg.get("msgId"),
                            msg.get("msgSeq"),
                            sender_name,
                            msg.get("senderQQNum"),
                            datetime.fromtimestamp(msg.get("msgTime", 0)).strftime('%Y-%m-%d %H:%M:%S'),
                            "".join(msg.get("elements", []))
                        ])
            
            print(f"成功导出 {len(processed_messages)} 条记录到文件：{output_filename}")

    except Exception as e:
        print(f"导出群聊记录时发生错误: {e}")

def export_c2c_chat_records(dbman, output_dir, export_format='json'):
    """
    导出所有私聊的聊天记录。
    """
    try:
        all_c2c_uins = dbman.c2c_messages().with_entities(PrivateMessage.contact_qq).distinct().all()
        if not all_c2c_uins:
            print("数据库中没有找到任何私聊记录。")
            return

        print(f"\n找到 {len(all_c2c_uins)} 个私聊。开始导出...")

        for uin_tuple in all_c2c_uins:
            target_peer_uin = uin_tuple[0]
            print(f"\n--- 正在导出与 {target_peer_uin} 的私聊消息 ---")

            messages_query = dbman.c2c_messages().filter_by(contact_qq=target_peer_uin).order_by(PrivateMessage.timestamp)
            db_messages = messages_query.all()

            if not db_messages:
                print(f"与 {target_peer_uin} 的私聊没有找到聊天记录。")
                continue

            processed_messages = []
            for dbo in db_messages:
                try:
                    elements_str = []
                    if dbo.message_body:
                        raw_elements, _ = blackboxprotobuf.decode_message(dbo.message_body)
                        elements_data = raw_elements.get("40800")
                        
                        if elements_data and not isinstance(elements_data, list):
                            elements_data = [elements_data]
                        
                        if elements_data:
                            for element_data in elements_data:
                                element_obj = Message.from_reply([element_data]).elements[0]
                                elements_str.append(str(element_obj))
                    
                    sender_nick_name = dbo.nick_name or "person"

                    processed_messages.append({
                        "msgId": dbo.ID,
                        "msgRandom": dbo.UNK_01,
                        "msgSeq": dbo.seq,
                        "chatType": dbo.UNK_03,
                        "msgType": dbo.UNK_04,
                        "subMsgTypepb": dbo.UNK_05,
                        "sendType": dbo.UNK_06,
                        "peeruid": dbo.contact_uid,
                        "peeruin": dbo.UNK_10,
                        "sendStatus": dbo.UNK_12,
                        "msgTime": dbo.timestamp,
                        "sendMemberName": dbo.UNK_15,
                        "sendNickName": sender_nick_name,
                        "senderQQNum": dbo.sender_qq,
                        "replyMsgSeq": dbo.UNK_26,
                        "elements": elements_str
                    })
                except Exception as e:
                    print(f"处理私聊消息ID {dbo.ID} 时出错: {e}")
            
            output_filename = os.path.join(output_dir, f"c2c_chat_history_{target_peer_uin}.{export_format}")
            
            if export_format == 'json':
                with open(output_filename, 'w', encoding='utf-8') as f:
                    json.dump(processed_messages, f, ensure_ascii=False, indent=4)
            elif export_format == 'txt':
                with open(output_filename, 'w', encoding='utf-8') as f:
                    for msg in processed_messages:
                        sender_nick_name = msg.get("sendNickName") or "person"
                        sender_qq = msg.get("senderQQNum")
                        message_content = "".join(msg.get("elements", []))
                        timestamp = datetime.fromtimestamp(msg.get("msgTime", 0)).strftime('%Y-%m-%d %H:%M:%S')
                        f.write(f"{sender_nick_name}({sender_qq}): {message_content} ({timestamp})\n")
            elif export_format == 'csv':
                with open(output_filename, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(["msgId", "msgSeq", "senderNickName", "senderQQNum", "msgTime", "elements"])
                    for msg in processed_messages:
                        sender_nick_name = msg.get("sendNickName") or "person"
                        writer.writerow([
                            msg.get("msgId"),
                            msg.get("msgSeq"),
                            sender_nick_name,
                            msg.get("senderQQNum"),
                            datetime.fromtimestamp(msg.get("msgTime", 0)).strftime('%Y-%m-%d %H:%M:%S'),
                            "".join(msg.get("elements", []))
                        ])

            print(f"成功导出 {len(processed_messages)} 条记录到文件：{output_filename}")
    
    except Exception as e:
        print(f"导出私聊记录时发生错误: {e}")


def main():
    """
    主函数，用于执行所有聊天记录的导出。
    """
    parser = argparse.ArgumentParser(description="导出聊天记录工具")
    parser.add_argument('--format', choices=['json', 'csv', 'txt'], default='json',
                        help='选择导出格式，默认为 json')
    args = parser.parse_args()
    
    dbman = DatabaseManager()
    output_dir = "chathistory"

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"已创建输出目录：{output_dir}")

    try:
        export_group_chat_records(dbman, output_dir, args.format)
        export_c2c_chat_records(dbman, output_dir, args.format)
        print(f"\n所有聊天记录已以 {args.format} 格式导出完成。")

    except KeyError:
        print("错误：数据库会话 'nt_msg' 未正确初始化。请确认 'nt_msg.decrypt.db' 文件存在。")
    except Exception as e:
        print(f"发生未知错误: {e}")

if __name__ == "__main__":
    main()