/**
 * Skill: contact-group-members
 * 管理联系人分组成员（增删）
 * 按姓名搜索 empId，精确匹配
 */
import { cworkClient } from '../shared/cwork-client.js';
import type { ContactGroupMembersInput, ContactGroupMembersOutput } from '../shared/types.js';

async function resolveEmpId(name: string): Promise<number> {
  const result = await cworkClient.searchEmpByName(name);
  // searchEmpByName 返回 inside.empList，精确匹配姓名
  const list = (result as any)?.inside?.empList ?? result ?? [];
  const exact = Array.isArray(list) ? list.filter((e: any) => String(e.name).trim() === name) : [];
  const candidates = exact.length > 0 ? exact : (Array.isArray(list) ? list : []);
  if (candidates.length === 0) throw new Error(`成员未找到: ${name}`);
  if (candidates.length > 1) throw new Error(`成员匹配不唯一: ${name}`);
  return Number(candidates[0].id ?? candidates[0].empId);
}

export async function contactGroupMembers(input: ContactGroupMembersInput): Promise<ContactGroupMembersOutput> {
  if (!input.groupName?.trim()) return { success: false, message: '分组名不能为空' };
  try {
    const groups = await cworkClient.queryContactGroups();
    const found = groups.find((g: any) => String(g.groupName).trim() === input.groupName.trim());
    if (!found) return { success: false, message: `未找到分组: ${input.groupName}` };

    const addEmpIds: number[] = [];
    for (const name of input.addNames ?? []) {
      addEmpIds.push(await resolveEmpId(name));
    }
    const removeEmpIds: number[] = [];
    for (const name of input.removeNames ?? []) {
      removeEmpIds.push(await resolveEmpId(name));
    }

    await cworkClient.manageGroupMembers(found.groupId, addEmpIds, removeEmpIds);
    return { success: true, data: {} };
  } catch (error) {
    return { success: false, message: `成员管理失败: ${error instanceof Error ? error.message : String(error)}` };
  }
}
