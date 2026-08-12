import { motion, AnimatePresence } from 'framer-motion'

// Tailwind needs full static class names to include them in the build - keep
// this map exhaustive rather than constructing class names dynamically.
const ACCENTS = {
  brand: 'bg-brand-100 text-brand-600 dark:bg-brand-900/40 dark:text-brand-300',
  orange: 'bg-orange-100 text-orange-600 dark:bg-orange-900/40 dark:text-orange-300',
  red: 'bg-red-100 text-red-600 dark:bg-red-900/40 dark:text-red-300',
  green: 'bg-green-100 text-green-600 dark:bg-green-900/40 dark:text-green-300',
  yellow: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300',
  sky: 'bg-sky-100 text-sky-600 dark:bg-sky-900/40 dark:text-sky-300',
  purple: 'bg-purple-100 text-purple-600 dark:bg-purple-900/40 dark:text-purple-300',
}

export default function MetricCard({ icon: Icon, label, value, unit, accent = 'brand', sub }) {
  return (
    <div className="glass-card p-4 flex flex-col gap-2 min-w-0">
      <div className="flex items-center justify-between">
        <span className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400 font-medium">
          {label}
        </span>
        {Icon && (
          <span className={`w-8 h-8 rounded-lg flex items-center justify-center text-lg ${ACCENTS[accent] || ACCENTS.brand}`}>
            <Icon />
          </span>
        )}
      </div>
      <AnimatePresence mode="wait">
        <motion.div
          key={value}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -6 }}
          transition={{ duration: 0.25 }}
          className="font-mono text-2xl font-semibold text-slate-800 dark:text-slate-100"
        >
          {value}
          {unit && <span className="text-sm font-normal text-slate-400 ml-1">{unit}</span>}
        </motion.div>
      </AnimatePresence>
      {sub && <span className="text-xs text-slate-400">{sub}</span>}
    </div>
  )
}
