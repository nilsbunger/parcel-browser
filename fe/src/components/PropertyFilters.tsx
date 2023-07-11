import { Button, Menu, NumberInput, Popover, Text } from "@mantine/core";
import {
  IconArrowsLeftRight,
  IconCirclePlus,
  IconMessageCircle,
  IconPhoto,
  IconSearch,
  IconSettings,
  IconTrash
} from "@tabler/icons";
import { useState } from "react";


function DropdownButton() {
  return <Menu shadow="md" width={200}>
    <Menu.Target>
      <Button><IconCirclePlus size={22}/></Button>
    </Menu.Target>

    <Menu.Dropdown>
      <Menu.Label>Application</Menu.Label>
      <Menu.Item icon={<IconSettings size={14}/>}>Lot size</Menu.Item>
      <Menu.Item icon={<IconMessageCircle size={14}/>}>Current zoning</Menu.Item>
      <Menu.Item icon={<IconPhoto size={14}/>}>Housing element</Menu.Item>
      <Menu.Item
        icon={<IconSearch size={14}/>}
        rightSection={<Text size="xs" color="dimmed">⌘K</Text>}
      >
        Search
      </Menu.Item>

      <Menu.Divider/>

      <Menu.Label>Danger zone</Menu.Label>
      <Menu.Item icon={<IconArrowsLeftRight size={14}/>}>Transfer my data</Menu.Item>
      <Menu.Item color="red" icon={<IconTrash size={14}/>}>Delete my account</Menu.Item>
    </Menu.Dropdown>
  </Menu>
}

function RangeButton() {
  const [opened, setOpened] = useState(false);
  const [minValue, setMinValue] = useState<number | ''>(0);
  const [maxValue, setMaxValue] = useState<number | ''>(0);
  const [btnText, setBtnText] = useState<string>("Lot size")

  const handlePopoverChange = (e) => {
    if (opened) {
      // popover is closing; update button text
      const btnText = (minValue && maxValue)
    ? `Lot size: ${minValue} - ${maxValue}`
    : minValue ? `Lot size: > ${minValue}`
      : maxValue ? `Lot size: < ${maxValue}`
        : 'Lot size'
      setBtnText(btnText)
    }
    setOpened((o) => !o)
  }
  return (
    <Popover width={200} position="bottom" withArrow shadow="md" opened={opened} onChange={handlePopoverChange}>
      <Popover.Target>
        <Button className="bg-inherit text-gray-800 border-gray-800 hover:bg-white" onClick={handlePopoverChange}
        >{btnText}</Button>
      </Popover.Target>
      <Popover.Dropdown>
        Lot size
        <div className="flex gap-5">
          <NumberInput min={0} max={99999} hideControls value={minValue} onChange={setMinValue} label="Min (sq ft)"/>
          <NumberInput min={1000} hideControls value={maxValue} onChange={setMaxValue} label="Max (sq ft)"/>
        </div>
      </Popover.Dropdown>
    </Popover>

  )
}

export default function PropertyFilters() {
  const onClick = (e) => {
    console.log("prop filter clicked")
  }
  return <div className="flex gap-5">
    <DropdownButton/>
    <RangeButton/>
  </div>
}
