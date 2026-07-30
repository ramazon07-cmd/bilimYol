import { BookOpenCheck } from "lucide-react";

type RbisBrandProps = {
  inverse?: boolean;
  className?: string;
};

export function RbisBrand({ inverse = false, className = "" }: RbisBrandProps) {
  return (
    <div className={`rbis-brand ${inverse ? "inverse" : ""} ${className}`.trim()}>
      <div className="rbis-brand-mark" aria-hidden="true">
        <BookOpenCheck size={23} strokeWidth={2.2} />
      </div>
      <div className="rbis-brand-copy">
        <strong>RBIS</strong>
        <small>Academic Diagnostic</small>
      </div>
    </div>
  );
}
