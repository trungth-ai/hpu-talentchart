// ★ Subdomain routing (CLAUDE.md Gotchas — đã setup ở middleware.ts)
// {org-slug}.talentchart.hpu.edu.vn → rewrite sang /career/{org-slug} (public career page)
// app.talentchart.hpu.edu.vn / localhost → admin app bình thường

import { NextResponse, type NextRequest } from 'next/server';

const BASE_DOMAIN = process.env.NEXT_PUBLIC_BASE_DOMAIN ?? 'talentchart.hpu.edu.vn';
const RESERVED_SUBDOMAINS = new Set(['app', 'www', 'storage', 'api']);

export function middleware(request: NextRequest) {
  // /api và /health do next.config rewrites xử lý — không rewrite tenant
  if (
    request.nextUrl.pathname.startsWith('/api') ||
    request.nextUrl.pathname === '/health'
  ) {
    return NextResponse.next();
  }

  const host = request.headers.get('host')?.split(':')[0].toLowerCase() ?? '';
  const suffix = `.${BASE_DOMAIN}`;

  // Không phải subdomain tenant → đi tiếp (admin app / localhost dev)
  if (!host.endsWith(suffix)) return NextResponse.next();

  const slug = host.slice(0, -suffix.length);
  if (!slug || slug.includes('.') || RESERVED_SUBDOMAINS.has(slug)) {
    return NextResponse.next();
  }

  // Career page công khai của tenant — rewrite giữ nguyên URL trên trình duyệt
  const url = request.nextUrl.clone();
  if (!url.pathname.startsWith('/career')) {
    url.pathname = `/career/${slug}${url.pathname === '/' ? '' : url.pathname}`;
    return NextResponse.rewrite(url);
  }
  return NextResponse.next();
}

export const config = {
  // Bỏ qua static assets và API routes của Next
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
};
