/**
 * Skill: my-feedback-list
 * 查询当前用户创建的反馈类型待办列表
 */

import { cworkClient } from '../shared/cwork-client.js';
import type { MyFeedbackListInput, MyFeedbackListOutput } from '../shared/types.js';

export async function myFeedbackList(input: MyFeedbackListInput): Promise<MyFeedbackListOutput> {
  const { pageSize = 30, pageIndex = 1 } = input;

  if (pageSize <= 0) return { success: false, message: 'pageSize 必须大于 0' };

  try {
    const result = await cworkClient.listCreatedFeedbacks(pageIndex, pageSize);
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
      message: `反馈列表查询失败: ${error instanceof Error ? error.message : String(error)}`,
    };
  }
}
