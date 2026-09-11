export async function checkBackendHealth() {
  try {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const response = await fetch(`${apiUrl}/api/v1/health`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      // Short timeout to not block UI development if backend is down
      signal: AbortSignal.timeout(3000)
    });
    
    if (!response.ok) {
      return { status: 'error', message: `Backend responded with status: ${response.status}` };
    }
    
    return await response.json();
  } catch (error) {
    return { status: 'error', message: 'Could not connect to backend' };
  }
}
