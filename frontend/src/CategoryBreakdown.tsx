import type { Dashboard } from './api'

export default function CategoryBreakdown({ categories }: { categories: Dashboard['categories'] }) {
  return (
    <details className="panel category-breakdown">
      <summary>Show category / supernumerary breakdown</summary>
      <p>Illustrative category breakdown — not an official compliance calculation.</p>
      <div className="stats">
        <div className="stat">
          <span>Base admissions</span>
          <strong>{categories.base_count}</strong>
          <small>Not marked supernumerary</small>
        </div>
        <div className="stat">
          <span>Supernumerary</span>
          <strong>{categories.supernumerary_count}</strong>
          <small>Part of active admissions</small>
        </div>
        <div className="stat">
          <span>NRI flag</span>
          <strong>{categories.nri_count}</strong>
          <small>Independent category flag</small>
        </div>
        <div className="stat">
          <span>OCI flag</span>
          <strong>{categories.oci_count}</strong>
          <small>Independent category flag</small>
        </div>
        <div className="stat">
          <span>Foreign-national flag</span>
          <strong>{categories.foreign_national_count}</strong>
          <small>Independent category flag</small>
        </div>
      </div>
      <p>
        Nationality flags can overlap with each other and the seat grouping. Do not add these
        columns together as a student total. This view does not change basic intake counts.
      </p>
      {categories.unclassified_count > 0 && (
        <p role="alert">
          {categories.unclassified_count} active records have an unclassified supernumerary flag.
        </p>
      )}
    </details>
  )
}
