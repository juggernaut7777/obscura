import { NextResponse } from 'next/server';
import { supabase } from '@/utils/supabase';

// Protect this route in a real app!
// For now, we'll just allow it for the demo admin dashboard

export async function GET(request) {
  try {
    // Fetch all orders
    const { data: orders, error } = await supabase
      .from('orders')
      .select('*')
      .order('created_at', { ascending: false });

    if (error) {
      console.error("[API ADMIN ORDERS GET] Supabase error:", error);
      return NextResponse.json({ success: false, error: error.message }, { status: 500 });
    }

    return NextResponse.json(orders || []);
  } catch (error) {
    console.error("[API ADMIN ORDERS GET] Error:", error);
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}

export async function POST(request) {
  try {
    const { orderId, action, tracking, pipeline } = await request.json();
    if (!orderId || !action) {
      return NextResponse.json({ success: false, error: "Missing orderId or action" }, { status: 400 });
    }

    let updateData = {};
    if (action === "mark-paid") {
      updateData = { status: 'paid' };
    } else if (action === "mark-combining") {
      updateData = { status: 'combining' };
    } else if (action === "mark-shipped") {
      if (!tracking || !pipeline) {
        return NextResponse.json({ success: false, error: "Missing tracking or pipeline info for shipping" }, { status: 400 });
      }
      updateData = { status: 'shipped', tracking, pipeline };
    } else {
      return NextResponse.json({ success: false, error: "Invalid action" }, { status: 400 });
    }

    const { data, error } = await supabase
      .from('orders')
      .update(updateData)
      .eq('id', orderId)
      .select();

    if (error) {
      console.error("[API ADMIN ORDERS POST] Supabase error:", error);
      return NextResponse.json({ success: false, error: error.message }, { status: 500 });
    }

    return NextResponse.json({ success: true, data });
  } catch (error) {
    console.error("[API ADMIN ORDERS POST] Error:", error);
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}
