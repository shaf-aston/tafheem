/**
 * The ring-and-number that closes a printed ayah: ۝ then the number in
 * Arabic-Indic digits, which the Quran face draws as one medallion.
 */
const DIGITS = new Intl.NumberFormat('ar-EG', { useGrouping: false })

export const ayahEnd = (n) => `۝${DIGITS.format(n)}`
