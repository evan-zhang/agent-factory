/**
 * Skill: task-manager-dashboard
 * 管理者视角：查看下属任务执行情况汇总
 */

import { cworkClient } from '../shared/cwork-client.js';
import type { TaskManagerDashboardInput, TaskManagerDashboardOutput } from '../shared/types.js';

export async function taskManagerDashboard(
  input: TaskManagerDashboardInput
): Promise<TaskManagerDashboardOutput> {
  const { subordinateIds = [], pageSize = 30, pageIndex = 1, taskStatus, reportStatus } = input;

  if (subordinateIds.length === 0) {
    return { success: false, message: '请提供下属员工 ID 列表（subordinateIds）' };
  }

  try {
    // 并发查询：下属任务列表 + 各自的待办数
    const [taskResult, todoResult] = await Promise.all([
      cworkClient.searchTaskPage({
        pageSize,
        pageIndex,
        empIdList: subordinateIds,
        status: taskStatus,
        reportStatus,
      } as any),
      cworkClient.getTodoList({ pageIndex: 1, pageSize: 100 } as any),
    ]);

    // 按任务状态分组统计
    const tasks = taskResult.list ?? [];
    const summary = {
      total: taskResult.total,
      inProgress: tasks.filter((t: any) => t.status === 1).length,
      closed: tasks.filter((t: any) => t.status === 0).length,
      pending: tasks.filter((t: any) => t.reportStatus === 1).length,  // 待汇报
      overdue: tasks.filter((t: any) => t.reportStatus === 3).length,  // 逾期
      reported: tasks.filter((t: any) => t.reportStatus === 2).length,  // 已汇报
    };

    // 按人员拆分任务
    const byPerson = subordinateIds.map(empId => {
      const personTasks = tasks.filter((t: any) =>
        t.reporterList?.some((r: any) => r.id === empId)
      );
      return {
        empId,
        taskCount: personTasks.length,
        inProgress: personTasks.filter((t: any) => t.status === 1).length,
        overdue: personTasks.filter((t: any) => t.reportStatus === 3).length,
        tasks: personTasks.map((t: any) => ({
          id: t.id,
          main: t.main,
          status: t.status,
          reportStatus: t.reportStatus,
          lastReportTime: t.lastReportTime,
          endTime: t.endTime,
        })),
      };
    });

    return {
      success: true,
      data: {
        summary,
        byPerson,
        total: taskResult.total,
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
