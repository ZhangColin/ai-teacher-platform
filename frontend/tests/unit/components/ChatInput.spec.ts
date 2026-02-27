/**
 * ChatInput组件单元测试
 */
import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import ChatInput from '@/components/chat/ChatInput.vue';

describe('ChatInput', () => {
  it('should render input and button', () => {
    const wrapper = mount(ChatInput);

    expect(wrapper.find('[data-testid="chat-input"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="send-button"]').exists()).toBe(true);
  });

  it('should emit send event with content when button clicked', async () => {
    const wrapper = mount(ChatInput);

    const input = wrapper.find('[data-testid="chat-input"]') as any;
    await input.setValue('Hello World');

    await wrapper.find('[data-testid="send-button"]').trigger('click');

    expect(wrapper.emitted('send')).toBeTruthy();
    expect(wrapper.emitted('send')?.[0]).toEqual(['Hello World']);
  });

  it('should emit send event when Enter pressed', async () => {
    const wrapper = mount(ChatInput);

    const input = wrapper.find('[data-testid="chat-input"]') as any;
    await input.setValue('Test');

    await input.trigger('keydown', { key: 'Enter' });

    expect(wrapper.emitted('send')).toBeTruthy();
  });

  it('should not send on Shift+Enter', async () => {
    const wrapper = mount(ChatInput);

    const input = wrapper.find('[data-testid="chat-input"]') as any;
    await input.setValue('Test');

    await input.trigger('keydown', { key: 'Enter', shiftKey: true });

    expect(wrapper.emitted('send')).toBeFalsy();
  });

  it('should disable send button when content is empty', async () => {
    const wrapper = mount(ChatInput);

    const button = wrapper.find('[data-testid="send-button"]');
    expect(button.attributes('disabled')).toBeDefined();
  });

  it('should enable send button when content exists', async () => {
    const wrapper = mount(ChatInput);

    const input = wrapper.find('[data-testid="chat-input"]') as any;
    await input.setValue('Hello');

    const button = wrapper.find('[data-testid="send-button"]');
    expect(button.attributes('disabled')).toBeUndefined();
  });

  it('should disable when isLoading prop is true', async () => {
    const wrapper = mount(ChatInput, {
      props: {
        isLoading: true,
      },
    });

    const button = wrapper.find('[data-testid="send-button"]');
    expect(button.attributes('disabled')).toBeDefined();
    expect(wrapper.find('[data-testid="loading-spinner"]').exists()).toBe(true);
  });
});
