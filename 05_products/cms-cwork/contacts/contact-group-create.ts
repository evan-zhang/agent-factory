/**
 * Skill: contact-group-create
 * 创建个人联系人分组
 */
import { cworkClient } from '../shared/cwork-client.js';
import type { ContactGroupCreateInput, ContactGroupCreateOutput } from '../shared/types.js';

export async function contactGroupCreate(input: ContactGroupCreateInput): Promise<ContactGroupCreateOutput> {
  if (!input.name?.trim()) return { success: false, message: '分组名不能为空' };
  try {
    const result = await cworkClient.saveOrUpdateContactGroup(input.name.trim());
    return { success: true, data: { groupId: result?.id } };
  } catch (error) {
    return { success: false, message: `创建分组失败: ${error instanceof Error ? error.message : String(error)}` };
  }
}
