import { Component, type ErrorInfo, type ReactNode } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Uncaught runtime error caught by boundary:", error, errorInfo);
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null });
    window.location.reload();
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-[400px] flex flex-col items-center justify-center p-8 border border-destructive/20 bg-destructive/5 rounded-2xl text-center max-w-xl mx-auto my-12 shadow-xs">
          <div className="p-4 bg-destructive/10 text-destructive rounded-full mb-6">
            <AlertTriangle className="h-10 w-10 animate-bounce" />
          </div>
          <h2 className="text-xl font-bold tracking-tight mb-2 text-destructive">
            Something went wrong
          </h2>
          <p className="text-muted-foreground text-sm max-w-md mb-8">
            An unexpected client-side runtime exception occurred: <br />
            <span className="font-mono text-xs bg-muted px-2 py-1 rounded-sm block mt-2 text-foreground">
              {this.state.error?.message || "Unknown error"}
            </span>
          </p>
          <button
            onClick={this.handleReset}
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-primary text-primary-foreground rounded-lg font-semibold text-sm hover:bg-primary/95 transition-colors shadow-xs"
          >
            <RefreshCw className="h-4 w-4" />
            Reload Application
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
