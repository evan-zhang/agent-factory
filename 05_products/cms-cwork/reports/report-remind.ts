/**
 * Skill: report-remind
 * 催办：向指定人员发送催促提醒（通过提交一条提醒类汇报实现）
 */

import { cworkClient } from '../shared/cwork-client.js';
import type { ReportRemindInput, ReportRemindOutput } from '../shared/types.js';

export async function reportRemind(input: ReportRemindInput): Promise<ReportRemindOutput> {
  const { empId, taskMain, deadline, content } = input;

  if (!empId) return { success: false, message: '催办对象 empId 不能为空' };
  if (!taskMain?.trim()) return { success: false, message: '任务名称不能为空' };

  const remindContent = content?.trim()
    || `请注意以下任务的进展需要更新：${taskMain}。`;

  try {
    const result = await cworkClient.submitReport({
      main: `【催办】${taskMain}`,
      contentHtml: `<p>${remindContent}</p>${deadline ? `<p>截止时间：${new Date(deadline).toLocaleDateString('zh-CN')}</p>` : ''}`,
      contentType: 'html',
      typeId: 9999,
      grade: '紧急',
      reportLevelList: [
        {
          level: 1,
          type: 'read',
          nodeName: '接收人',
          levelUserList: [{ empId }],
        },
      ],
    });

    return {
      success: true,
      data: {
        reportId: result.id,
        remindedEmpId: empId,
        message: `已向 ${empId} 发送催办提醒`,
      },
    };
  } catch (error) {
    return {
      success: false,
      message: `催办失败: ${error instanceof Error ? error.message : String(error)}`,
    };
  }
}
