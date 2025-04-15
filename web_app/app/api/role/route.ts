import { NextResponse } from 'next/server';

export async function GET(request: Request) {
  const token = request.headers.get('Authorization');

  try {
    // make sure to have an .env.local file at root of the project with API_URL defined 
    const response = await fetch(`${process.env.API_URL}/prod/role`, {
      method: 'GET',
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
