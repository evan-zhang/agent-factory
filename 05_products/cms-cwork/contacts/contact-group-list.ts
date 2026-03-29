/**
 * Skill: contact-group-list
 * 列出个人联系人分组
 */
import { cworkClient } from '../shared/cwork-client.js';
import type { ContactGroupListInput, ContactGroupListOutput } from '../shared/types.js';

export async function contactGroupList(input: ContactGroupListInput = {}): Promise<ContactGroupListOutput> {
  try {
    const groups = await cworkClient.queryContactGroups(input.checkEmpId);
    return { success: true, data: { groups } };
  } catch (error) {
    return { success: false, message: `查询分组失败: ${error instanceof Error ? error.message : String(error)}` };
  }
}
