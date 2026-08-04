"use client";
import { useState, useEffect } from "react";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import styles from "./page.module.css";

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState("orders");
  const [orders, setOrders] = useState([]);
  const [stagedItems, setStagedItems] = useState([]);
  const [loadingOrders, setLoadingOrders] = useState(true);
  const [loadingStaged, setLoadingStaged] = useState(true);
  const [orderFilter, setOrderFilter] = useState("all");
  const [expandedOrders, setExpandedOrders] = useState({});
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncOutput, setSyncOutput] = useState("");
  
  // Authentication state
  const [adminSecret, setAdminSecret] = useState("");
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Shipping Modal states
  const [shippingModalOpen, setShippingModalOpen] = useState(false);
  const [selectedOrderId, setSelectedOrderId] = useState("");
  const [trackingNumber, setTrackingNumber] = useState("");
  const [shippingPipeline, setShippingPipeline] = useState("kakobuy");
  const [isShippingSubmit, setIsShippingSubmit] = useState(false);

  useEffect(() => {
    if (isAuthenticated) {
      fetchOrders();
      fetchStagedItems();
    }
  }, [isAuthenticated]);

  const getAuthHeaders = () => ({
    "Authorization": `Bearer ${adminSecret}`
  });

  const handleLogin = (e) => {
    e.preventDefault();
    if (adminSecret.trim()) {
      setIsAuthenticated(true);
    }
  };

  const fetchOrders = async () => {
    setLoadingOrders(true);
    try {
      const res = await fetch("/api/admin/orders", {
        headers: getAuthHeaders()
      });
      if (res.status === 401) {
        setIsAuthenticated(false);
        alert("Unauthorized or Invalid Admin Secret.");
        return;
      }
      const data = await res.json();
      if (Array.isArray(data)) {
        setOrders(data);
      }
    } catch (e) {
      console.error("Error fetching orders:", e);
    } finally {
      setLoadingOrders(false);
    }
  };

  const fetchStagedItems = async () => {
    setLoadingStaged(true);
    try {
      const res = await fetch("/api/admin/warehouse", {
        headers: getAuthHeaders()
      });
      if (res.status === 401) {
        setIsAuthenticated(false);
        alert("Unauthorized or Invalid Admin Secret.");
        return;
      }
      const data = await res.json();
      if (Array.isArray(data)) {
        setStagedItems(data);
      }
    } catch (e) {
      console.error("Error fetching staged items:", e);
    } finally {
      setLoadingStaged(false);
    }
  };

  const toggleOrderExpand = (orderId) => {
    setExpandedOrders(prev => ({
      ...prev,
      [orderId]: !prev[orderId]
    }));
  };

  const handleOrderAction = async (orderId, action, extraParams = {}) => {
    const confirmMsg = action === "mark-paid" ? 
      "Are you sure you want to mark this order as purchased?" :
      "Are you sure you want to mark this order as combining shipping?";
    
    if (action !== "mark-shipped" && !confirm(confirmMsg)) return;

    try {
      const res = await fetch("/api/admin/orders", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...getAuthHeaders()
        },
        body: JSON.stringify({
          orderId,
          action,
          ...extraParams
        })
      });

      if (res.status === 401) {
        setIsAuthenticated(false);
        alert("Unauthorized or Session Expired.");
        return;
      }

      const result = await res.json();
      if (result.success) {
        alert("Order updated successfully!");
        fetchOrders();
      } else {
        alert(`Update failed: ${result.error || "Unknown error"}`);
      }
    } catch (e) {
      alert(`Update failed: ${e.message}`);
    }
  };

  const openShippingModal = (orderId) => {
    setSelectedOrderId(orderId);
    setTrackingNumber("");
    setShippingPipeline("kakobuy");
    setShippingModalOpen(true);
  };

  const handleShippingSubmit = async (e) => {
    e.preventDefault();
    if (!trackingNumber || !shippingPipeline) {
      alert("Please provide both a tracking number and a carrier/pipeline.");
      return;
    }
    
    setIsShippingSubmit(true);
    try {
      await handleOrderAction(selectedOrderId, "mark-shipped", {
        tracking: trackingNumber,
        pipeline: shippingPipeline
      });
      setShippingModalOpen(false);
    } finally {
      setIsShippingSubmit(false);
    }
  };

  const handleTriggerSync = async () => {
    setIsSyncing(true);
    setSyncOutput("Initializing Catalog Sync...\nScanning OUTPUT_READY_FOR_SALE folder...\n");
    try {
      const res = await fetch("/api/admin/upload", {
        method: "POST",
        headers: getAuthHeaders()
      });

      if (res.status === 401) {
        setIsAuthenticated(false);
        alert("Unauthorized or Session Expired.");
        return;
      }

      const data = await res.json();
      if (data.success) {
        setSyncOutput(prev => prev + "\n[SUCCESS] Sync complete!\n\n" + data.output);
      } else {
        setSyncOutput(prev => prev + "\n[ERROR] Sync failed:\n" + (data.error || "Unknown error"));
      }
    } catch (e) {
      setSyncOutput(prev => prev + "\n[ERROR] Request failed:\n" + e.message);
    } finally {
      setIsSyncing(false);
    }
  };

  // Filter logic
  const filteredOrders = orders.filter(order => {
    if (orderFilter === "all") return true;
    if (orderFilter === "pending") return order.status === "pending" || order.status === "awaiting_payment";
    if (orderFilter === "combining") return order.status === "combining" || order.status === "in_warehouse";
    return order.status === orderFilter;
  });

  // Stats
  const stats = {
    pendingCount: orders.filter(o => o.status === "pending" || o.status === "awaiting_payment").length,
    combiningCount: orders.filter(o => o.status === "combining" || o.status === "in_warehouse").length,
    shippedCount: orders.filter(o => o.status === "shipped").length,
    warehouseCount: stagedItems.length
  };

  return (
    <>
      <Header cartCount={0} onCartClick={() => {}} />
      <main className={styles.main}>
        <div className={`container ${styles.adminContainer}`}>
          
          {!isAuthenticated ? (
            <div style={{ maxWidth: '400px', margin: '4rem auto', textAlign: 'center' }}>
              <h1 className={styles.title} style={{ marginBottom: '1.5rem' }}>Admin Login</h1>
              <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <input
                  type="password"
                  placeholder="Enter Admin Secret"
                  value={adminSecret}
                  onChange={(e) => setAdminSecret(e.target.value)}
                  style={{ padding: '0.75rem', borderRadius: '4px', border: '1px solid #ccc', fontSize: '1rem' }}
                  required
                />
                <button
                  type="submit"
                  className={styles.sysBtn}
                >
                  Access Dashboard
                </button>
              </form>
            </div>
          ) : (
            <>
          {/* Header section */}
          <header className={styles.header}>
            <div>
              <span className="text-caption">OBSCURA Console</span>
              <h1 className={styles.title}>Admin Panel</h1>
              <button
                onClick={() => setIsAuthenticated(false)}
                className={styles.sysBtn}
                style={{ marginTop: '0.5rem', padding: '0.25rem 0.75rem', fontSize: '0.8rem', backgroundColor: '#666' }}
              >
                Logout
              </button>
            </div>
            
            <nav className={styles.navTabs}>
              <button 
                className={`${styles.tabBtn} ${activeTab === "orders" ? styles.activeTab : ""}`}
                onClick={() => setActiveTab("orders")}
              >
                Orders ({orders.length})
              </button>
              <button 
                className={`${styles.tabBtn} ${activeTab === "warehouse" ? styles.activeTab : ""}`}
                onClick={() => setActiveTab("warehouse")}
              >
                Staged Items ({stagedItems.length})
              </button>
              <button 
                className={`${styles.tabBtn} ${activeTab === "control" ? styles.activeTab : ""}`}
                onClick={() => setActiveTab("control")}
              >
                System Control
              </button>
            </nav>
          </header>

          {/* Stats Bar */}
          <section className={styles.statsGrid}>
            <div className={styles.statCard}>
              <span className={styles.statLabel}>Pending Orders</span>
              <div className={styles.statValue}>{stats.pendingCount}</div>
            </div>
            <div className={styles.statCard}>
              <span className={styles.statLabel}>Awaiting Consolidation</span>
              <div className={styles.statValue}>{stats.combiningCount}</div>
            </div>
            <div className={styles.statCard}>
              <span className={styles.statLabel}>Total Shipped</span>
              <div className={styles.statValue}>{stats.shippedCount}</div>
            </div>
            <div className={styles.statCard}>
              <span className={styles.statLabel}>Staged Basics (Warehouse)</span>
              <div className={styles.statValue}>{stats.warehouseCount}</div>
            </div>
          </section>

          {/* Content sections */}
          {activeTab === "orders" && (
            <section className={styles.contentSection}>
              {/* Order filters */}
              <div className={styles.filters} style={{ marginBottom: "2rem", display: "flex", gap: "10px" }}>
                {["all", "pending", "purchased", "combining", "shipped"].map((filt) => (
                  <button 
                    key={filt}
                    className={`${styles.tabBtn} ${orderFilter === filt ? styles.activeTab : ""}`}
                    onClick={() => setOrderFilter(filt)}
                    style={{ padding: "0.5rem 1rem", fontSize: "0.8rem" }}
                  >
                    {filt.toUpperCase()}
                  </button>
                ))}
              </div>

              {loadingOrders ? (
                <div style={{ textAlign: "center", padding: "4rem" }}>Loading orders...</div>
              ) : filteredOrders.length === 0 ? (
                <div style={{ textAlign: "center", padding: "4rem", color: "#666" }}>No orders found.</div>
              ) : (
                <div className={styles.ordersList}>
                  {filteredOrders.map((order) => {
                    const isOpen = !!expandedOrders[order.order_id];
                    return (
                      <div key={order.order_id} className={styles.orderCard}>
                        {/* Header bar */}
                        <div 
                          className={styles.orderHeader}
                          onClick={() => toggleOrderExpand(order.order_id)}
                        >
                          <div className={styles.orderMainInfo}>
                            <span className={styles.orderId}>{order.order_id}</span>
                            <span className={styles.orderDate}>
                              {new Date(order.created_at).toLocaleDateString()} {new Date(order.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                            </span>
                            <span className={styles.customerName}>
                              {order.customer?.name || "Unknown"}
                            </span>
                          </div>
                          
                          <div style={{ display: "flex", alignItems: "center", gap: "1.5rem" }}>
                            <span className={`${styles.orderBadge} ${styles['badge-' + order.status]}`}>
                              {order.status.replace("_", " ")}
                            </span>
                            <span className={styles.orderTotal}>
                              ${order.financials?.total_usd?.toFixed(2)}
                            </span>
                            <span>{isOpen ? "▲" : "▼"}</span>
                          </div>
                        </div>

                        {/* Collapsible Details */}
                        {isOpen && (
                          <div className={styles.orderDetails}>
                            <div className={styles.detailsGrid}>
                              {/* Left Column: Buyer */}
                              <div className={styles.buyerInfo}>
                                <h3 className={styles.detailsColTitle}>Buyer Info</h3>
                                <p><strong>Email:</strong> {order.customer?.email}</p>
                                <p><strong>Address:</strong> {order.customer?.address}</p>
                                <p><strong>Country:</strong> {order.customer?.country}</p>
                                <p><strong>Shipping Paid:</strong> ${order.financials?.shipping_paid_usd?.toFixed(2)}</p>
                              </div>

                              {/* Right Column: Items */}
                              <div>
                                <h3 className={styles.detailsColTitle}>Order Items</h3>
                                <div className={styles.itemsList}>
                                  {order.items?.map((item, idx) => (
                                    <div key={idx} className={styles.itemRow}>
                                      <div>
                                        <div className={styles.itemName}>{item.name}</div>
                                        <div className={styles.itemMeta}>
                                          Size: {item.size || "OS"} | Color: {item.color || "Default"} | Qty: {item.qty}
                                        </div>
                                      </div>
                                      <div className={styles.itemPrice}>
                                        ${(item.price_usd * item.qty).toFixed(2)}
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            </div>

                            {/* Sourcing Links */}
                            {order.pipelines?.kakobuy?.order_urls?.length > 0 && (
                              <div className={styles.sourcingLinks}>
                                <h4 className={styles.sourcingTitle}>Kakobuy Affiliate / Sourcing Links</h4>
                                <div className={styles.sourcingList}>
                                  {order.pipelines.kakobuy.order_urls.map((linkObj, idx) => (
                                    <div key={idx} style={{ marginBottom: "0.5rem" }}>
                                      <span style={{ fontSize: "0.85rem", color: "#aaa" }}>{linkObj.item}: </span>
                                      <a 
                                        href={linkObj.url} 
                                        target="_blank" 
                                        rel="noopener noreferrer" 
                                        className={styles.sourcingLink}
                                      >
                                        {linkObj.url}
                                      </a>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* Status actions */}
                            <div className={styles.orderActions}>
                              {(order.status === "pending" || order.status === "awaiting_payment") && (
                                <button 
                                  className={`${styles.actionBtn} ${styles.btnPaid}`}
                                  onClick={() => handleOrderAction(order.order_id, "mark-paid")}
                                >
                                  Mark as Purchased
                                </button>
                              )}
                              {(order.status === "purchased" || order.status === "in_warehouse") && (
                                <button 
                                  className={styles.actionBtn}
                                  onClick={() => handleOrderAction(order.order_id, "mark-combining")}
                                >
                                  Mark as Combining
                                </button>
                              )}
                              {order.status !== "shipped" && order.status !== "cancelled" && (
                                <button 
                                  className={`${styles.actionBtn} ${styles.btnShip}`}
                                  onClick={() => openShippingModal(order.order_id)}
                                >
                                  Mark as Shipped
                                </button>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </section>
          )}

          {activeTab === "warehouse" && (
            <section className={styles.contentSection}>
              {loadingStaged ? (
                <div style={{ textAlign: "center", padding: "4rem" }}>Scanning MANUAL_CURATION queue...</div>
              ) : stagedItems.length === 0 ? (
                <div style={{ textAlign: "center", padding: "4rem", color: "#666" }}>No staged items found in MANUAL_CURATION.</div>
              ) : (
                <div className={styles.warehouseGrid}>
                  {stagedItems.map((item) => (
                    <div key={item.folderName} className={styles.warehouseCard}>
                      <div className={styles.cardImgWrap}>
                        {item.thumbnail ? (
                          <img src={item.thumbnail} alt={item.metadata?.product_name} className={styles.cardImg} />
                        ) : (
                          <div className={styles.noCardImg}>No Preview Image</div>
                        )}
                        {item.metadata?.price_cny > 0 && (
                          <div className={styles.cardMeta}>¥{item.metadata.price_cny}</div>
                        )}
                      </div>
                      
                      <div className={styles.cardBody}>
                        <h3 className={styles.cardTitle}>{item.metadata?.product_name || "Staged Item"}</h3>
                        <span className={styles.cardCategory}>{item.metadata?.category || "uncategorized"}</span>
                        
                        <div className={styles.cardDetails}>
                          <span>Color:</span>
                          <span>{item.metadata?.color || "default"}</span>
                        </div>
                        <div className={styles.cardDetails}>
                          <span>Size Info:</span>
                          <span style={{ fontSize: "0.8rem" }}>{item.metadata?.size_info || "None"}</span>
                        </div>
                        <div className={styles.cardDetails}>
                          <span>Photos:</span>
                          <span>{item.metadata?.image_count || 1} angle(s)</span>
                        </div>

                        {item.metadata?.seller_contact && (
                          <div style={{ marginTop: "1rem", fontSize: "0.8rem", color: "#666" }}>
                            {item.metadata.seller_contact.whatsapp && (
                              <div>WA: <span style={{ color: "#aaa" }}>{item.metadata.seller_contact.whatsapp}</span></div>
                            )}
                            {item.metadata.seller_contact.wechat && (
                              <div>WX: <span style={{ color: "#aaa" }}>{item.metadata.seller_contact.wechat}</span></div>
                            )}
                          </div>
                        )}
                        
                        {item.metadata?.link && (
                          <div className={styles.cardFooter}>
                            <a 
                              href={item.metadata.link} 
                              target="_blank" 
                              rel="noopener noreferrer" 
                              className={styles.cardSupplierLink}
                              title={item.metadata.link}
                            >
                              Sourcing Link →
                            </a>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>
          )}

          {activeTab === "control" && (
            <section className={styles.contentSection}>
              <div className={styles.controlGrid}>
                {/* Left col: triggers */}
                <div className={styles.controlCol}>
                  <div>
                    <h2 className={styles.controlTitle}>Uploader Sync</h2>
                    <p className={styles.controlDesc}>
                      Triggers the catalog uploader script to scan completed AI generated lookbooks under `OUTPUT_READY_FOR_SALE`, stage assets, and merge new listings into the active web storefront.
                    </p>
                  </div>
                  <button 
                    className={styles.sysBtn}
                    onClick={handleTriggerSync}
                    disabled={isSyncing}
                  >
                    {isSyncing ? "Running Uploader..." : "Run Catalog Uploader"}
                  </button>
                </div>

                {/* Right col: stdout log console */}
                <div>
                  <h3 className={styles.detailsColTitle} style={{ marginBottom: "0.5rem" }}>System Console Log</h3>
                  <div className={styles.logConsole}>
                    {syncOutput ? (
                      syncOutput
                    ) : (
                      <div className={styles.logEmpty}>Console idle. Waiting for task execution.</div>
                    )}
                  </div>
                </div>
              </div>
            </section>
          )}
            </>
          )}

        </div>
      </main>

      {/* Shipping Modal */}
      {shippingModalOpen && (
        <div className={styles.modalOverlay} onClick={() => setShippingModalOpen(false)}>
          <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
            <button 
              className={styles.closeBtn} 
              style={{ position: "absolute", right: "1.5rem", top: "1rem", background: "none", border: "none", fontSize: "1.5rem", color: "#666", cursor: "pointer" }}
              onClick={() => setShippingModalOpen(false)}
            >
              &times;
            </button>
            <h2 className={styles.modalTitle}>SHIP ORDER #{selectedOrderId}</h2>
            
            <form className={styles.modalForm} onSubmit={handleShippingSubmit}>
              <div>
                <label className={styles.modalLabel}>Carrier / Pipeline</label>
                <select 
                  className={styles.modalSelect}
                  value={shippingPipeline}
                  onChange={(e) => setShippingPipeline(e.target.value)}
                >
                  <option value="kakobuy">Kakobuy (Pipeline A)</option>
                  <option value="cj">CJ Dropshipping (Pipeline B)</option>
                  <option value="manual">Manual / Private Agent</option>
                </select>
              </div>
              
              <div>
                <label className={styles.modalLabel}>International Tracking Number</label>
                <input 
                  type="text"
                  placeholder="e.g. YT1234567890CN or LN987654321US"
                  className={styles.modalInput}
                  value={trackingNumber}
                  onChange={(e) => setTrackingNumber(e.target.value)}
                  required
                />
              </div>
              
              <div className={styles.modalActions}>
                <button 
                  type="button" 
                  className={styles.modalCancelBtn}
                  onClick={() => setShippingModalOpen(false)}
                >
                  Cancel
                </button>
                <button 
                  type="submit" 
                  className={styles.modalSubmitBtn}
                  disabled={isShippingSubmit}
                >
                  {isShippingSubmit ? "Submitting..." : "Ship Order"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <Footer />
    </>
  );
}
