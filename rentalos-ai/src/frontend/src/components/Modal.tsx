import { ReactNode } from 'react'

interface ModalProps {
  title: string
  open: boolean
  onClose: () => void
  children: ReactNode
}

const Modal = ({ title, open, onClose, children }: ModalProps) => {
  if (!open) return null
  return (
    <div className="fixed inset-0 flex items-center justify-center bg-slate-950/80">
      <div className="w-full max-w-lg rounded-2xl bg-slate-900 p-6">
        <header className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">{title}</h3>
          <button className="text-slate-400" onClick={onClose}>
            Close
          </button>
        </header>
        <div className="mt-4 space-y-3">{children}</div>
      </div>
    </div>
  )
}

export default Modal
