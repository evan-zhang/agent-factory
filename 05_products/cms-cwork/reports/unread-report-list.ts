/**
 * Skill: unread-report-list
 * 获取当前用户的未读汇报列表
 */

import { cworkClient } from '../shared/cwork-client.js';
import type { UnreadReportListInput, UnreadReportListOutput } from '../shared/types.js';

export async function unreadReportList(input: UnreadReportListInput): Promise<UnreadReportListOutput> {
  const { pageSize = 30, pageIndex = 1 } = input;

  if (pageSize <= 0) return { success: false, message: 'pageSize 必须大于 0' };

  try {
    const result = await cworkClient.getUnreadList({ pageIndex, pageSize } as any);
    return {
      success: true,
      data: {
        total: (result as any).total ?? 0,
        list: (result as any).list ?? [],
        pageIndex,
        pageSize,
      },
    };
  } catch (error) {
    return {
      success: false,
      message: `未读汇报查询失败: ${error instanceof Error ? error.message : String(error)}`,
    };
  }
}
