import { Component, type ErrorInfo, type ReactNode } from 'react';

type ErrorBoundaryProps = {
  children: ReactNode;
  /** 出错时展示的标题，默认为通用文案。 */
  title?: string;
};

type ErrorBoundaryState = {
  hasError: boolean;
};

/** 局部错误边界：某一块内容渲染异常时只降级该区域，不让整页白屏。 */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { hasError: false };

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { hasError: true };
  }

  componentDidCatch(error: unknown, info: ErrorInfo) {
    console.error('ErrorBoundary 捕获到渲染异常', error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="border border-amber-200 bg-amber-50 p-4" style={{ borderRadius: 8 }}>
          <p className="text-sm font-semibold text-amber-950">{this.props.title ?? '内容渲染出错'}</p>
          <p className="mt-1 text-sm leading-6 text-amber-900">该区域渲染时发生异常，其余内容不受影响。</p>
          <button
            type="button"
            className="secondary-btn mt-3 px-3 text-xs"
            onClick={() => this.setState({ hasError: false })}
          >
            重试
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

/** 路由级错误页：用于 react-router 的 errorElement。 */
export function RouteErrorFallback() {
  return (
    <div className="flex min-h-[60vh] items-center justify-center p-6">
      <div className="w-full max-w-md border border-stone-200 bg-white p-6 text-center shadow-sm" style={{ borderRadius: 8 }}>
        <p className="text-lg font-semibold text-stone-900">页面出现了一点问题</p>
        <p className="mt-2 text-sm leading-6 text-stone-600">页面加载或渲染时发生异常，请重试；若持续出现请检查后端服务状态。</p>
        <button type="button" className="primary-btn mt-4 w-full justify-center" onClick={() => window.location.reload()}>
          重试
        </button>
      </div>
    </div>
  );
}
