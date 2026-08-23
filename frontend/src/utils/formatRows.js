export const formatRows = (n) => {
  if (n == null) return '0'
  if (n >= 1_000_000_000) return `${(n / 1e9).toFixed(1)}B`
  if (n >= 1_000_000) return `${(n / 1e6).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1e3).toFixed(0)}K`
  return n.toLocaleString()
}
