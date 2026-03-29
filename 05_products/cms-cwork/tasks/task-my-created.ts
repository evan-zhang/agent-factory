/**
 * Skill: task-my-created
 * 查询我创建的任务
 * 支持按分配对象（下属）筛选
 */

import { cworkClient } from '../shared/cwork-client.js';
import type { TaskMyCreatedInput, TaskMyCreatedOutput } from '../shared/types.js';

export async function taskMyCreated(
  input: TaskMyCreatedInput
): Promise<TaskMyCreatedOutput> {
  const {
    pageSize = 30,
    pageIndex = 1,
    status,
    assigneeIds,   // 按分配对象筛选（下属 ID 列表）
  } = input;

  if (pageSize <= 0) return { success: false, message: 'pageSize 必须大于 0' };

  try {
    // empIdList 筛选参与人（含汇报人、责任人的等价角色）
    const params: any = {
      pageSize,
      pageIndex,
      status,
    };

    if (assigneeIds && assigneeIds.length > 0) {
      // 按分配的对象筛选（下属）
      params.empIdList = assigneeIds;
    }

    const result = await cworkClient.searchTaskPage(params);

    // 如果指定了下属，进一步过滤出当前用户创建的
    // （empIdList 筛的是参与人，不是创建人，需要任务链详情确认创建人）
    // 注：当前 API 层级筛选存在精度限制，此处返回"参与人包含指定下属"的任务
    return {
      success: true,
      data: {
        total: result.total,
        list: result.list ?? [],
        pageIndex,
        pageSize,
        filterApplied: assigneeIds ? `分配给: ${assigneeIds.join(', ')}` : '全部任务',
      },
    };
  } catch (error) {
    return {
      success: false,
      message: `查询失败: ${error instanceof Error ? error.message : String(error)}`,
    };
  }
}
