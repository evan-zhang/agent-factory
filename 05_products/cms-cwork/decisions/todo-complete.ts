/**
 * Skill: todo-complete
 * 完成待办（建议/决策/反馈）
 * 决策类需传 operate（agree/disagree）
 */

import { cworkClient } from '../shared/cwork-client.js';
import type { TodoCompleteInput, TodoCompleteOutput } from '../shared/types.js';

export async function todoComplete(input: TodoCompleteInput): Promise<TodoCompleteOutput> {
  const { todoId, content, operate } = input;

  if (!todoId) return { success: false, message: 'todoId 不能为空' };

  // 决策类必须指定 operate
  if (operate && !['agree', 'disagree'].includes(operate)) {
    return { success: false, message: '决策类操作只能是 agree（同意）或 disagree（不同意）' };
  }

  try {
    await cworkClient.completeTodo(todoId, content ?? '', operate);
    return {
      success: true,
      data: { todoId, operate, message: '待办已处理' },
    };
  } catch (error) {
    return {
      success: false,
      message: `待办处理失败: ${error instanceof Error ? error.message : String(error)}`,
    };
  }
}
