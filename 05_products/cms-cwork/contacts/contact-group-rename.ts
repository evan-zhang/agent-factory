/**
 * Skill: contact-group-rename
 * 重命名个人联系人分组
 */
import { cworkClient } from '../shared/cwork-client.js';
import type { ContactGroupRenameInput, ContactGroupRenameOutput } from '../shared/types.js';

export async function contactGroupRename(input: ContactGroupRenameInput): Promise<ContactGroupRenameOutput> {
  if (!input.groupName?.trim()) return { success: false, message: '原分组名不能为空' };
  if (!input.newName?.trim()) return { success: false, message: '新分组名不能为空' };
  try {
    const groups = await cworkClient.queryContactGroups();
    const found = groups.find((g: any) => String(g.groupName).trim() === input.groupName.trim());
    if (!found) return { success: false, message: `未找到分组: ${input.groupName}` };
    await cworkClient.saveOrUpdateContactGroup(input.newName.trim(), found.groupId);
    return { success: true, data: {} };
  } catch (error) {
    return { success: false, message: `重命名失败: ${error instanceof Error ? error.message : String(error)}` };
  }
}
