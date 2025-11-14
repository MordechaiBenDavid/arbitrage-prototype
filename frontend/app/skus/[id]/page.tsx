import TimelineView from "../../../components/TimelineView";

export default function SkuDetailPage({ params }: { params: { id: string } }) {
  return <TimelineView skuId={Number(params.id)} />;
}
