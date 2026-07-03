const examples = ['最近 7 天销售额是多少？', '哪个商品品类退款率最高？', '最近 30 天支付失败率是多少？', '按月查看新增用户趋势'];

export function ExampleQuestionChips() {
  return (
    <div className="flex flex-wrap gap-2">
      {examples.map((example) => (
        <button key={example} className="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-600 transition hover:border-cyan-300 hover:text-cyan-700">
          {example}
        </button>
      ))}
    </div>
  );
}
