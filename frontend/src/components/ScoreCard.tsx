export default function ScoreCard({ score, tips }: { score: number; tips: string[] }) {
  const color = score >= 75 ? "text-emerald-300" : score >= 50 ? "text-amber-300" : "text-rose-300";
  return (
    <div className="card">
      <h3 className="mb-2 text-sm text-slate-400">Financial Health Score</h3>
      <div className={`text-4xl font-bold ${color}`}>{score.toFixed(0)} / 100</div>
      <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-slate-300">
        {tips.slice(0, 3).map((tip) => (
          <li key={tip}>{tip}</li>
        ))}
      </ul>
    </div>
  );
}
