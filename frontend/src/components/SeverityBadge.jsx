const STYLES = {
  Green: 'bg-severity-green/15 text-green-700 dark:text-green-300 ring-severity-green/40',
  Yellow: 'bg-severity-yellow/15 text-yellow-700 dark:text-yellow-300 ring-severity-yellow/40',
  Orange: 'bg-severity-orange/15 text-orange-700 dark:text-orange-300 ring-severity-orange/40',
  Red: 'bg-severity-red/15 text-red-700 dark:text-red-300 ring-severity-red/40',
  Extreme: 'bg-severity-extreme/15 text-red-900 dark:text-red-200 ring-severity-extreme/50',
}

export default function SeverityBadge({ level }) {
  const style = STYLES[level] || STYLES.Green
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ring-1 ${style}`}>
      <span className="w-1.5 h-1.5 rounded-full bg-current" />
      {level}
    </span>
  )
}
