import { ReactNode } from 'react'

interface NavBarProps {
  title: string
  rightSlot?: ReactNode
}

const NavBar = ({ title, rightSlot }: NavBarProps) => (
  <header className="flex items-center justify-between border-b border-slate-800 px-6 py-4 bg-slate-900/80">
    <h1 className="text-xl font-semibold tracking-wide">{title}</h1>
    <div>{rightSlot}</div>
  </header>
)

export default NavBar
