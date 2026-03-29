/**
 * Skill: report-reply
 * 对指定汇报进行回复
 */

import { cworkClient } from '../shared/cwork-client.js';
import type { ReportReplyInput, ReportReplyOutput } from '../shared/types.js';

export async function reportReply(input: ReportReplyInput): Promise<ReportReplyOutput> {
  const { reportRecordId, contentHtml, addEmpIdList, sendMsg = true } = input;

  if (!reportRecordId?.trim()) return { success: false, message: 'reportRecordId 不能为空' };
  if (!contentHtml?.trim()) return { success: false, message: '回复内容不能为空' };

  try {
    const replyId = await cworkClient.replyReport({
      reportRecordId: reportRecordId.trim(),
      contentHtml: contentHtml.trim(),
      addEmpIdList: addEmpIdList?.length ? addEmpIdList : undefined,
      sendMsg,
    });
    return { success: true, data: { replyId: String(replyId) } };
  } catch (error) {
    return { success: false, message: `回复失败: ${error instanceof Error ? error.message : String(error)}` };
  }
}
