/**
 * Skill: task-my-assigned
 * 查询分配给我的任务（我是责任人）
 */

import { cworkClient } from '../shared/cwork-client.js';
import type { TaskMyAssignedInput, TaskMyAssignedOutput } from '../shared/types.js';

export async function taskMyAssigned(
  input: TaskMyAssignedInput
): Promise<TaskMyAssignedOutput> {
  const { pageSize = 30, pageIndex = 1, status } = input;

  if (pageSize <= 0) return { success: false, message: 'pageSize 必须大于 0' };

  try {
    // empIdList 传当前用户 ID，系统返回该用户涉及的所有任务
    // status: 0=关闭、1=进行中、2=未启动
    const result = await cworkClient.searchTaskPage({
      pageSize,
      pageIndex,
      empIdList: [input.userId],
      status,
    } as any);

    // 从结果中过滤出我是责任人的任务
    const myAssigned = (result.list ?? []).filter((task: any) => {
      const reporters = task.reporterList ?? [];
      return reporters.some((r: any) => r.id === input.userId);
    });

    return {
      success: true,
      data: {
        total: myAssigned.length,
        list: myAssigned,
        pageIndex,
        pageSize,
      },
    };
  } catch (error) {
    return {
      success: false,
      message: `查询失败: ${error instanceof Error ? error.message : String(error)}`,
    };
  }
}
