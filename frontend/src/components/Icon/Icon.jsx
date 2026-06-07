// Renders a UI icon that may be EITHER an emoji/glyph string (e.g. "📍", "⊞")
// OR an image path under /icons/ (served statically from public/icons/).
// This lets nav items, stat cards and destination lists mix both kinds freely:
// pass a glyph and it renders inline like before; pass "/icons/foo.jpeg" and it
// renders a sized <img>. Sizing is in `em` so each call site's container font
// keeps controlling the icon scale, just as it did for the emoji it replaced.
const IMAGE_ICON = /^\/icons\//;

export default function Icon({ icon, alt = '' }) {
  if (typeof icon === 'string' && IMAGE_ICON.test(icon)) {
    return (
      <img
        src={icon}
        alt={alt}
        style={{
          width: '1.25em',
          height: '1.25em',
          objectFit: 'contain',
          borderRadius: '0.25em',
          verticalAlign: 'middle',
        }}
      />
    );
  }
  return <>{icon}</>;
}
