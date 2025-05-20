const ApprovedLabel = (
    {
        approved,
        isMobile
    }
    :
    {
        approved: boolean,
        isMobile: boolean
    }) => {
    return (
        <div
            style={isMobile ? {
                marginBottom: "20px",
            } : undefined}
        >
            {approved && <span>
                (✅{" "}Подтвержденные)
            </span>}
            {!approved && <span>
                (⏳{" "}Не подтвержденные)
            </span>}
        </div>
    )
}

export default ApprovedLabel;