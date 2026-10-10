import { notFound } from 'next/navigation';
import PosterEditor from './PosterEditor';

export const dynamic = 'force-dynamic';

export default function Page() {
  if (process.env.ANNOTATION_ENABLED !== 'true') notFound();
  return <PosterEditor />;
}
