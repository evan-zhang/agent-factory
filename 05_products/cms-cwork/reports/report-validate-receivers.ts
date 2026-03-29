/**
 * Skill: report-validate-receivers
 * 按姓名模糊搜索，校验接收人是否存在
 * 返回匹配列表供用户确认（姓名+部门），无需编号
 */

import { cworkClient } from '../shared/cwork-client.js';
import type { ReportValidateReceiversInput, ReportValidateReceiversOutput } from '../shared/types.js';

export async function reportValidateReceivers(
  input: ReportValidateReceiversInput
): Promise<ReportValidateReceiversOutput> {
  const { names = [] } = input;

  if (names.length === 0) {
    return { success: false, message: '接收人姓名列表为空，请提供至少一个姓名' };
  }

  try {
    const results: Array<{
      name: string;
      status: 'found' | 'multiple' | 'not_found';
      employees: Array<{ empId: string; name: string; title: string; dept: string }>;
    }> = [];

    // 逐个姓名搜索
    for (const name of names) {
      const result = await cworkClient.searchEmpByName(name);
      const matches = (result.inside?.empList ?? []).map(emp => ({
        empId: emp.id,
        name: emp.name,
        title: emp.title ?? '',
        dept: emp.mainDept ?? '',
      }));

      if (matches.length === 0) {
        results.push({ name, status: 'not_found', employees: [] });
      } else if (matches.length === 1) {
        results.push({ name, status: 'found', employees: matches });
      } else {
        results.push({ name, status: 'multiple', employees: matches });
      }
    }

    // 检查是否有未找到的
    const notFound = results.filter(r => r.status === 'not_found');
    if (notFound.length > 0) {
      return {
        success: false,
        message: `未找到以下姓名对应的员工: ${notFound.map(r => r.name).join(', ')}，请检查姓名或直接提供员工 ID`,
      };
    }

    // 检查是否有多个匹配的
    const multiple = results.filter(r => r.status === 'multiple');
    if (multiple.length > 0) {
      const ambiguousList = multiple.map(r => {
        const options = r.employees.map(e => `    - ${e.name}（${e.title}，${e.dept}）`).join('\n');
        return `  "${r.name}" 匹配到多人，请重新输入更精确的姓名或直接提供员工 ID：\n${options}`;
      }).join('\n');
      return {
        success: false,
        message: `以下姓名匹配到多人，需要更精确的姓名：\n${ambiguousList}`,
      };
    }

    // 全部精确匹配，生成确认 Prompt
    const confirmList = results.map(r => {
      const emp = r.employees[0];
      return `  ✓ ${emp.name}（${emp.dept}）`;
    }).join('\n');

    return {
      success: true,
      data: {
        validatedCount: results.length,
        confirmedEmployees: results.map(r => ({
          empId: r.employees[0].empId,
          name: r.employees[0].name,
          title: r.employees[0].title,
          dept: r.employees[0].dept,
        })),
        confirmPrompt: `【接收人确认】

将向以下人员发送汇报：

${confirmList}

---
以上人员是否正确？回复"是"确认，或告诉我需要修改的姓名。`,
      },
    };
  } catch (error) {
    return {
      success: false,
      message: `接收人校验失败: ${error instanceof Error ? error.message : String(error)}`,
    };
  }
}
