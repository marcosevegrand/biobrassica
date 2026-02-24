export type InstagramPost = {
  url: string;
  image: string;
  caption: string;
};

const INSTAGRAM_USERNAME = 'biobrassica';

async function fetchInstagramViaGraphApi(limit: number): Promise<InstagramPost[]> {
  const accessToken = import.meta.env.INSTAGRAM_GRAPH_ACCESS_TOKEN;
  const igUserId = import.meta.env.INSTAGRAM_IG_USER_ID;

  if (!accessToken || !igUserId) return [];

  const fields = [
    'id',
    'caption',
    'media_type',
    'media_url',
    'thumbnail_url',
    'permalink',
    'timestamp',
  ].join(',');

  const url = `https://graph.facebook.com/v20.0/${igUserId}/media?fields=${fields}&limit=${limit}&access_token=${accessToken}`;
  const response = await fetch(url);
  if (!response.ok) return [];

  const payload = await response.json();
  const items = payload?.data ?? [];

  return items
    .map((item: any) => {
      const image = item?.media_type === 'VIDEO'
        ? item?.thumbnail_url || item?.media_url
        : item?.media_url;

      return {
        url: item?.permalink || `https://www.instagram.com/${INSTAGRAM_USERNAME}/`,
        image: image || '',
        caption: item?.caption || 'Instagram Biobrassica',
      } as InstagramPost;
    })
    .filter((post: InstagramPost) => Boolean(post.image));
}

async function fetchInstagramViaPublicEndpoint(limit: number): Promise<InstagramPost[]> {
  const response = await fetch(`https://www.instagram.com/api/v1/users/web_profile_info/?username=${INSTAGRAM_USERNAME}`, {
    headers: {
      'x-ig-app-id': '936619743392459',
      'user-agent': 'Mozilla/5.0',
    },
  });

  if (!response.ok) return [];

  const data = await response.json();
  const edges = data?.data?.user?.edge_owner_to_timeline_media?.edges ?? [];

  return edges
    .slice(0, limit)
    .map((edge: any) => {
      const node = edge?.node ?? {};
      const caption = node?.edge_media_to_caption?.edges?.[0]?.node?.text ?? 'Instagram Biobrassica';
      return {
        url: node?.shortcode ? `https://www.instagram.com/p/${node.shortcode}/` : `https://www.instagram.com/${INSTAGRAM_USERNAME}/`,
        image: node?.thumbnail_src ?? node?.display_url ?? '',
        caption,
      } as InstagramPost;
    })
    .filter((post: InstagramPost) => Boolean(post.image));
}

export async function getInstagramPosts(limit = 6): Promise<InstagramPost[]> {
  try {
    const graphPosts = await fetchInstagramViaGraphApi(limit);
    if (graphPosts.length > 0) return graphPosts;
  } catch {
  }

  try {
    const publicPosts = await fetchInstagramViaPublicEndpoint(limit);
    if (publicPosts.length > 0) return publicPosts;
  } catch {
  }

  return [];
}
