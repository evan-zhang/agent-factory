/**
 * Skill: report-read-mark
 * 标记指定汇报为已读，清除未读通知
 */

import { cworkClient } from '../shared/cwork-client.js';
import type { ReportReadMarkInput, ReportReadMarkOutput } from '../shared/types.js';

export async function reportReadMark(input: ReportReadMarkInput): Promise<ReportReadMarkOutput> {
  const { reportId } = input;

  if (!reportId) return { success: false, message: 'reportId 不能为空' };

  try {
    await cworkClient.markReportRead(reportId);
    return { success: true, data: { reportId, message: '已标记为已读' } };
  } catch (error) {
    return { success: false, message: `标记已读失败: ${error instanceof Error ? error.message : String(error)}` };
  }
}
