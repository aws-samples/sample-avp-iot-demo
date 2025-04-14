import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  const token = request.headers.get('Authorization');
  
  try {
    const { searchParams } = new URL(request.url);
    const s3Path = searchParams.get('s3Path');

    // Construct the API URL with query parameters
    const apiUrl = `${process.env.API_URL}/prod/download?s3Path=${encodeURIComponent(s3Path || '')}`;

    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Authorization': token || '',
      },
    });

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
