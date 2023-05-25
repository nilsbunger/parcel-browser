// CollapsibleTreeNode.tsx
import React, { useState } from "react"

interface CollapsibleTreeNodeProps {
  label: string
  children?: React.ReactNode
}
interface CollapsibleTreeProps {
  data: Record<string, any>
  prefix?: string
}

const CollapsibleTree: React.FC<CollapsibleTreeProps> = ({ data, prefix = "" }) => {
  return (
    <ul style={{ paddingLeft: 0 }}>
      {Object.entries(data).map(([key, value]) => {
        const currentPath = prefix ? `${prefix}.${key}` : key
        if (typeof value === "object" && value !== null && !Array.isArray(value)) {
          return (
            <CollapsibleTreeNode key={currentPath} label={key}>
              <CollapsibleTree data={value} prefix={currentPath} />
            </CollapsibleTreeNode>
          )
        } else {
          return <li key={currentPath}>{`${key}: ${value}`}</li>
        }
      })}
    </ul>
  )
}

const CollapsibleTreeNode: React.FC<CollapsibleTreeNodeProps> = ({ label, children }) => {
  const [isOpen, setIsOpen] = useState(false)

  const handleClick = () => {
    setIsOpen(!isOpen)
  }

  return (
    <li style={{ listStyleType: "none" }}>
      <span onClick={handleClick} style={{ cursor: "pointer", marginLeft: "-1rem" }}>
        {isOpen ? "▼ " : "▶ "}
        {label}
      </span>
      {isOpen && <ul style={{ paddingLeft: "1.5rem" }}>{children}</ul>}
    </li>
  )
}

export default CollapsibleTree
