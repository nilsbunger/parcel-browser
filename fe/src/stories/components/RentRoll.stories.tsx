
import type { Meta, StoryObj } from '@storybook/react';
import RentRoll from "../../components/RentRoll";


//👇 This default export determines where your story goes in the story list
const meta: Meta<typeof RentRoll> = {
  component: RentRoll,
};

export default meta;
type Story = StoryObj<typeof RentRoll>;

export const FirstStory: Story = {
  args: {
    //👇 The args you need here will depend on your component
    rows: [],
  },
};
