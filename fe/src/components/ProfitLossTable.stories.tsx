
import type { Meta, StoryObj } from '@storybook/react';
import ProfitLossTable from "./ProfitLossTable";


//👇 This default export determines where your story goes in the story list
const meta: Meta<typeof ProfitLossTable> = {
  component: ProfitLossTable,
};

export default meta;
type Story = StoryObj<typeof ProfitLossTable>;

export const FirstStory: Story = {
  args: {
    //👇 The args you need here will depend on your component
  },
};
