import { MagnifyingGlassIcon } from '@heroicons/react/24/outline';
import { Listbox, Transition } from '@headlessui/react';
import { Fragment, useMemo } from 'react';

interface Props {
  sources: string[];
  selectedSource: string;
  onFilterChange(source: string): void;
  onQueryChange(query: string): void;
}

export default function SearchBar({
  sources,
  selectedSource,
  onFilterChange,
  onQueryChange,
}: Props) {
  const options = useMemo(() => ['All sources', ...sources], [sources]);

  return (
    <section className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
      <div className="relative w-full max-w-xl">
        <MagnifyingGlassIcon
          className="pointer-events-none absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-500"
          aria-hidden="true"
        />
        <input
          aria-label="Search articles"
          className="w-full rounded-full border border-slate-700/40 bg-slate-900/70 py-3 pl-10 pr-4 text-slate-100 shadow-inner transition focus:border-sky-400/70 focus:bg-slate-900/90"
          placeholder="Search headlines or descriptions"
          onChange={(event) => onQueryChange(event.target.value)}
        />
      </div>

      <Listbox value={selectedSource} onChange={onFilterChange}>
        <div className="relative w-full max-w-xs">
          <Listbox.Button className="w-full rounded-full border border-slate-700/40 bg-slate-900/70 px-4 py-3 text-left text-slate-100 shadow-inner transition focus:border-sky-400/70 focus:bg-slate-900/90">
            <span>{selectedSource || 'All sources'}</span>
          </Listbox.Button>
          <Transition
            as={Fragment}
            leave="transition ease-in duration-100"
            leaveFrom="opacity-100"
            leaveTo="opacity-0"
          >
            <Listbox.Options className="absolute z-10 mt-2 max-h-60 w-full overflow-auto rounded-2xl border border-slate-700/40 bg-slate-900/90 p-2 text-sm text-slate-100 shadow-xl backdrop-blur">
              {options.map((option) => (
                <Listbox.Option
                  key={option}
                  value={option === 'All sources' ? '' : option}
                  className={({ active }) =>
                    `cursor-pointer rounded-xl px-3 py-2 transition ${
                      active ? 'bg-sky-500/20 text-sky-100' : 'text-slate-100'
                    }`
                  }
                >
                  {option}
                </Listbox.Option>
              ))}
            </Listbox.Options>
          </Transition>
        </div>
      </Listbox>
    </section>
  );
}
