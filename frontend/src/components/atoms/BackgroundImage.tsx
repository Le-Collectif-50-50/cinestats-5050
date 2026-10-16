export default function BackgroundImage() {
  return (
    <picture className="background-image" aria-hidden="true">
      <source srcSet="/home.avif" type="image/avif" />
      <source srcSet="/home.webp" type="image/webp" />
      {/* Native picture selection avoids downloading an extra fallback image. */}
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src="/home.jpg"
        alt=""
        width={1920}
        height={1013}
        loading="eager"
        fetchPriority="high"
      />
    </picture>
  );
}
