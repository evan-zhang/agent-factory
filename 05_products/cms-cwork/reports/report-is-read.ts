/**
 * Skill: report-is-read
 * 判断指定员工是否已读某汇报
 */

import { cworkClient } from '../shared/cwork-client.js';
import type { ReportIsReadInput, ReportIsReadOutput } from '../shared/types.js';

export async function reportIsRead(input: ReportIsReadInput): Promise<ReportIsReadOutput> {
  const { reportId, employeeId } = input;

  if (!reportId) return { success: false, message: 'reportId 不能为空' };
  if (!employeeId) return { success: false, message: 'employeeId 不能为空' };

  try {
    const isRead = await cworkClient.isReportRead(reportId, employeeId);
    return {
      success: true,
      data: {
        reportId,
        employeeId,
        isRead,
        status: isRead ? '已读' : '未读',
      },
    };
  } catch (error) {
    return {
      success: false,
      message: `查询失败: ${error instanceof Error ? error.message : String(error)}`,
    };
  }
}
